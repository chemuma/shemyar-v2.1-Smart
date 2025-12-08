from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CommandHandler, CallbackQueryHandler
from database.db import get_db
from database.models import User
from config import CHANNEL_USERNAME, CHANNEL_ID, SENIOR_ADMINS
from utils.validators import validate_persian_name, validate_national_code, validate_student_id
from utils.helpers import format_phone
from keyboards.user import user_main_menu

# استیت‌ها
STUDENT_ID, FULL_NAME, NATIONAL_CODE, PHONE, CONFIRM_ALL = range(5)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = next(get_db())
    existing = db.query(User).filter(User.user_id == user.id).first()
    
    if existing:
        is_admin = existing.is_admin or user.id in SENIOR_ADMINS
        await update.message.reply_text(
            f"خوش برگشتی {existing.full_name.split()[0]} عزیز!",
            reply_markup=user_main_menu(is_admin)
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"سلام {user.first_name} عزیز\n"
        "به ربات رسمی انجمن علمی مهندسی شیمی دانشگاه محقق اردبیلی خوش آمدی!\n\n"
        "برای ادامه، ابتدا در کانال رسمی عضو شو:\n"
        f"{CHANNEL_USERNAME}",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عضو شدم", callback_data="check_join")]])
    )
    return STUDENT_ID

async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        member = await query.bot.get_chat_member(CHANNEL_ID, query.from_user.id)
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception()
    except:
        await query.edit_message_text(
            f"هنوز عضو کانال نشدی\nلطفاً اول عضو شو:\n{CHANNEL_USERNAME}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("عضو شدم", callback_data="check_join")]])
        )
        return STUDENT_ID

    await query.edit_message_text(
        "عالی! حالا لطفاً شماره دانشجویی خودت رو وارد کن:\n\n"
        "اگر دانشجوی دانشگاه محقق اردبیلی نیستی، عدد ۰۰ را وارد کن تا به عنوان مهمان ثبت‌نام کنی."
    )
    return STUDENT_ID

async def get_student_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = update.message.text.strip()
    result = validate_student_id(sid)
    if result == "invalid":
        await update.message.reply_text(
            "متأسفم، شماره دانشجویی وارد شده جزو دانشجویان دانشکده فنی و مهندسی نیست.\n\n"
            "لطفاً دوباره وارد کن یا عدد ۰۰ را بفرست تا به عنوان مهمان ثبت‌نام کنی."
        )
        return STUDENT_ID

    context.user_data["student_id"] = sid if sid != "00" else None
    context.user_data["is_guest"] = (sid == "00")

    if sid == "00":
        await update.message.reply_text("شما به عنوان مهمان ثبت‌نام می‌کنید.\nلطفاً نام و نام خانوادگی خودت رو به فارسی وارد کن:")
        return FULL_NAME

    suggested = f"{update.effective_user.first_name or ''} {update.effective_user.last_name or ''}".strip()
    if suggested and len(suggested) > 4 and " " in suggested:
        context.user_data["temp_name"] = suggested
        await update.message.reply_text(
            f"نام و نام خانوادگی شما:\n{suggested}\n\nدرست است؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("بله", callback_data="name_ok")],
                [InlineKeyboardButton("اصلاح", callback_data="name_edit")]
            ])
        )
    else:
        await update.message.reply_text("لطفاً نام و نام خانوادگی خودت رو به فارسی وارد کن:")
    return FULL_NAME

# ادامه در پیام بعدی (محدودیت کاراکتر)
# فقط بگو «ادامه بده» و من بقیه start.py + بقیه فایل‌ها رو کامل و بی‌نقص برات می‌فرستم

منتظرم!
