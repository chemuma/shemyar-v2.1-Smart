# handlers/admin_tools.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from database.db import get_db
from database.models import User
from config import SENIOR_ADMINS, OPERATORS_GROUP
from keyboards.user import user_main_menu

# استیت‌ها
BLOCK_ADD, BLOCK_REMOVE, ADMIN_ADD, ADMIN_REMOVE = range(4)

# منوی بلاک لیست
async def blocklist_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("اضافه کردن به بلاک لیست", callback_data="block_add_start")],
        [InlineKeyboardButton("حذف از بلاک لیست", callback_data="block_remove_start")],
        [InlineKeyboardButton("برگشت به منوی ادمین", callback_data="back_to_admin")]
    ]
    await query.edit_message_text("مدیریت بلاک لیست:", reply_markup=InlineKeyboardMarkup(keyboard))

# اضافه کردن به بلاک لیست
async def block_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("آیدی عددی کاربر را بفرست (مثلاً 123456789):")
    return BLOCK_ADD

async def block_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("آیدی باید فقط عدد باشد!")
        return BLOCK_ADD
    
    user_id = int(text)
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        await update.message.reply_text("این کاربر در دیتابیس نیست!")
        return BLOCK_ADD
    
    if user.is_blocked:
        await update.message.reply_text("این کاربر قبلاً بلاک شده است!")
        return BLOCK_ADD
    
    user.is_blocked = True
    db.commit()
    
    await update.message.reply_text(f"کاربر {user.full_name} با موفقیت بلاک شد")
    return ConversationHandler.END

# حذف از بلاک لیست
async def block_remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("آیدی عددی کاربر را بفرست تا از بلاک لیست خارج شود:")
    return BLOCK_REMOVE

async def unblock_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("آیدی باید فقط عدد باشد!")
        return BLOCK_REMOVE
    
    user_id = int(text)
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        await update.message.reply_text("کاربر پیدا نشد!")
        return BLOCK_REMOVE
    
    if not user.is_blocked:
        await update.message.reply_text("این کاربر بلاک نیست!")
        return BLOCK_REMOVE
    
    user.is_blocked = False
    db.commit()
    
    await update.message.reply_text(f"کاربر {user.full_name} از بلاک لیست خارج شد")
    return ConversationHandler.END

# مدیریت ادمین‌ها (فقط ارشد)
async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in SENIOR_ADMINS:
        await query.edit_message_text("فقط ادمین ارشد می‌تواند ادمین اضافه/حذف کند!")
        return ConversationHandler.END
    
    keyboard = [
        [InlineKeyboardButton("اضافه کردن ادمین", callback_data="admin_add_start")],
        [InlineKeyboardButton("حذف ادمین", callback_data="admin_remove_start")],
        [InlineKeyboardButton("برگشت", callback_data="back_to_admin")]
    ]
    await query.edit_message_text("مدیریت ادمین‌ها:", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("آیدی عددی ادمین جدید را بفرست:")
    return ADMIN_ADD

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("آیدی باید عدد باشد!")
        return ADMIN_ADD
    
    user_id = int(text)
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        await update.message.reply_text("این کاربر در دیتابیس نیست!")
        return ADMIN_ADD
    
    user.is_admin = True
    db.commit()
    
    await update.message.reply_text(f"{user.full_name} به عنوان ادمین اضافه شد")
    return ConversationHandler.END

# شروع دوباره برای همه
async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if user and user.is_blocked:
        await update.message.reply_text("شما دسترسی به ربات ندارید.")
        return
    
    context.user_data.clear()
    context.chat_data.clear()
    
    is_admin = user.is_admin if user else False
    await update.message.reply_text(
        "ربات با موفقیت ری‌استارت شد!\nحالا می‌تونی دوباره شروع کنی",
        reply_markup=user_main_menu(is_admin)
    )

# هندلرهای Conversation
admin_tools_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(blocklist_menu, pattern="^admin_blocklist$"),
        CallbackQueryHandler(manage_admins, pattern="^admin_manage_admins$")
    ],
    states={
        BLOCK_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, block_user)],
        BLOCK_REMOVE: [MessageHandler(filters.TEXT & ~filters.COMMAND, unblock_user)],
        ADMIN_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin)]
    },
    fallbacks=[],
    per_user=False
)
