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

# تأیید نام پیشنهادی از تلگرام
async def handle_suggested_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "name_ok":
        context.user_data["full_name"] = context.user_data["temp_name"]
        await query.edit_message_text("نام تأیید شد.\nحالا کد ملی ۱۰ رقمی خودت رو وارد کن:")
        return NATIONAL_CODE
    else:
        await query.edit_message_text("نام و نام خانوادگی رو به فارسی وارد کن:")
        return FULL_NAME

# دریافت و تأیید نام کامل
async def get_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if not validate_persian_name(name):
        await update.message.reply_text("نام باید فارسی باشه، حداقل ۶ حرف و شامل فاصله.\nدوباره وارد کن:")
        return FULL_NAME

    context.user_data["full_name"] = name
    await update.message.reply_text(
        f"نام و نام خانوادگی: {name}\n\nدرست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله", callback_data="confirm_name")],
            [InlineKeyboardButton("اصلاح", callback_data="edit_name")]
        ])
    )
    return NATIONAL_CODE

async def confirm_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "edit_name":
        await query.edit_message_text("نام و نام خانوادگی رو دوباره وارد کن:")
        return FULL_NAME
    await query.edit_message_text("نام تأیید شد.\nحالا کد ملی ۱۰ رقمی خودت رو وارد کن:")
    return NATIONAL_CODE

# دریافت و تأیید کد ملی
async def get_national_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if not validate_national_code(code):
        await update.message.reply_text("کد ملی نامعتبر است!\nدوباره وارد کن:")
        return NATIONAL_CODE

    context.user_data["national_code"] = code
    await update.message.reply_text(
        f"کد ملی: {code}\n\nدرست است؟",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله", callback_data="confirm_nc")],
            [InlineKeyboardButton("اصلاح", callback_data="edit_nc")]
        ])
    )
    return PHONE

async def confirm_national_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "edit_nc":
        await query.edit_message_text("کد ملی رو دوباره وارد کن:")
        return NATIONAL_CODE
    await query.edit_message_text(
        "حالا شماره موبایلت رو وارد کن یا دکمه زیر رو بزن:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره تماس"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return PHONE

# دریافت و تأیید شماره تلفن
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.contact:
        phone = format_phone(update.message.contact.phone_number)
    else:
        phone = format_phone(update.message.text.strip())

    if not (phone.startswith("09") and len(phone) == 11):
        await update.message.reply_text("شماره موبایل باید با ۰۹ شروع بشه و ۱۱ رقمی باشه!")
        return PHONE

    context.user_data["phone"] = phone

    # خلاصه نهایی
    info = f"""
خلاصه اطلاعات شما:

نام: {context.user_data['full_name']}
کد ملی: {context.user_data['national_code']}
شماره دانشجویی: {context.user_data['student_id'] or 'مهمان'}
تلفن: {phone}

همه چیز درسته؟
    """
    await update.message.reply_text(
        info,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله، ثبت‌نام کن", callback_data="final_yes")],
            [InlineKeyboardButton("اصلاح اطلاعات", callback_data="final_edit")]
        ])
    )
    return CONFIRM_ALL

# تأیید نهایی و ذخیره
async def final_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "final_edit":
        await query.edit_message_text(
            "کدام بخش رو می‌خوای اصلاح کنی؟",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("نام و نام خانوادگی", callback_data="edit_name_final")],
                [InlineKeyboardButton("کد ملی", callback_data="edit_nc_final")],
                [InlineKeyboardButton("شماره تلفن", callback_data="edit_phone_final")],
                [InlineKeyboardButton("ادامه ثبت‌نام", callback_data="final_yes")]
            ])
        )
        return CONFIRM_ALL

    # ذخیره در دیتابیس
    db = next(get_db())
    new_user = User(
        user_id=update.effective_user.id,
        full_name=context.user_data["full_name"],
        national_code=context.user_data["national_code"],
        student_id=context.user_data["student_id"],
        phone=context.user_data["phone"],
        is_admin=update.effective_user.id in SENIOR_ADMINS,
        is_senior_admin=update.effective_user.id in SENIOR_ADMINS
    )
    db.add(new_user)
    db.commit()

    await query.edit_message_text(
        "تبریک! ثبت‌نام با موفقیت انجام شد.\nحالا می‌تونی از تمام امکانات ربات استفاده کنی:",
        reply_markup=user_main_menu(new_user.is_admin or new_user.is_senior_admin)
    )
    context.user_data.clear()
    return ConversationHandler.END

# ConversationHandler اصلی
start_conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        STUDENT_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_student_id),
                     CallbackQueryHandler(check_membership, pattern="^check_join$")],
        FULL_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_full_name),
                    CallbackQueryHandler(handle_suggested_name, pattern="^name_")],
        NATIONAL_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_national_code),
                        CallbackQueryHandler(confirm_name, pattern="^(confirm_name|edit_name)$")],
        PHONE: [MessageHandler(filters.TEXT | filters.CONTACT, get_phone),
                CallbackQueryHandler(confirm_national_code, pattern="^(confirm_nc|edit_nc)$")],
        CONFIRM_ALL: [CallbackQueryHandler(final_confirm, pattern="^(final_yes|final_edit|edit_.*_final)$")]
    },
    fallbacks=[],
    per_user=True
)

