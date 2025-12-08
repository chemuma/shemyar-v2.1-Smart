# handlers/events.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from database.db import get_db
from database.models import Event, Registration, User
from config import OPERATORS_GROUP, BANK_CARD, CARD_OWNER
from utils.helpers import get_first_name
from utils.excel_exporter import create_registration_excel
import jdatetime
from datetime import datetime

REG_CONFIRM, WAIT_RECEIPT = range(2)

# نمایش لیست رویدادهای فعال
async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = next(get_db())
    events = db.query(Event).filter(Event.status == "active").all()
    
    if not events:
        text = "در حال حاضر رویداد فعالی وجود ندارد"
        await (update.callback_query or update.message).reply_text(text)
        return
    
    keyboard = []
    for e in events:
        cap = "نامحدود" if e.capacity == 0 else f"{e.remaining_capacity}/{e.capacity}"
        cost = "رایگان" if e.cost == 0 else f"{e.cost:,} تومان"
        keyboard.append([InlineKeyboardButton(f"{e.title} | {cost} | {cap}", callback_data=f"event_detail_{e.id}")])
    
    await (update.callback_query or update.message).reply_text(
        "رویدادهای فعال:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# جزئیات رویداد
async def event_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[-1])
    db = next(get_db())
    event = db.get(Event, event_id)
    if not event or event.status != "active":
        await query.edit_message_text("این رویداد دیگر فعال نیست.")
        return
    
    text = f"""
<b>{event.title}</b>

{event.description}

تاریخ: {event.date_shamsi}
محل: {event.location}
هزینه: {'رایگان' if event.cost == 0 else f'{event.cost:,} تومان'}
ظرفیت باقی‌مانده: {'نامحدود' if event.capacity == 0 else f'{event.remaining_capacity} نفر'}

هشتگ: {event.hashtag}
"""
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ثبت‌نام در رویداد", callback_data=f"event_reg_{event.id}")]])
    )

# شروع ثبت‌نام
async def start_registration(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    event_id = int(query.data.split("_")[-1])
    user_id = query.from_user.id
    db = next(get_db())
    event = db.get(Event, event_id)
    
    if not event or event.status != "active":
        await query.edit_message_text("رویداد فعال نیست.")
        return
    
    if db.query(Registration).filter(Registration.event_id == event_id, Registration.user_id == user_id).first():
        await query.edit_message_text("شما قبلاً در این رویداد ثبت‌نام کرده‌اید")
        return
    
    if event.capacity > 0 and event.remaining_capacity <= 0:
        await query.edit_message_text("متأسفیم، ظرفیت اصلی پر شده است")
        return
    
    context.user_data["reg_event_id"] = event_id
    
    if event.cost == 0:
        await register_free(event, user_id, query, context)
        return
    
    # غیررایگان — کاهش ظرفیت کمکی
    if event.auxiliary_capacity <= 0:
        await query.edit_message_text("به دلیل ازدحام، موقتاً ثبت‌نام متوقف شده. چند دقیقه دیگر تلاش کنید.")
        return
    
    event.auxiliary_capacity -= 1
    db.commit()
    
    await query.edit_message_text(
        f"رویداد: <b>{event.title}</b>\nمبلغ: <b>{event.cost:,} تومان</b>\n\nآیا مایل به ثبت‌نام هستید؟",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("بله، ادامه بده", callback_data="reg_yes")],
            [InlineKeyboardButton("خیر، انصراف", callback_data="reg_no")]
        ])
    )
    return REG_CONFIRM

async def register_free(event, user_id, query, context):
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    row = db.query(Registration).filter(Registration.event_id == event.id).count() + 1
    
    reg = Registration(event_id=event.id, user_id=user_id, row_number=row, payment_status="confirmed")
    db.add(reg)
    if event.capacity > 0:
        event.remaining_capacity -= 1
    db.commit()
    
    msg = f"""
#ثبت_نام_جدید #{event.hashtag.replace('#','')}

ردیف: {row}
نام: {user.full_name}
کد ملی: {user.national_code}
شماره دانشجویی: {user.student_id or 'مهمان'}
تلفن: {user.phone}
"""
    await context.bot.send_message(OPERATORS_GROUP, msg)
    await query.edit_message_text("ثبت‌نام با موفقیت انجام شد!")

# تأیید ثبت‌نام غیررایگان
async def confirm_paid_reg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "reg_no":
        db = next(get_db())
        event = db.get(Event, context.user_data["reg_event_id"])
        event.auxiliary_capacity += 1
        db.commit()
        await query.edit_message_text("ثبت‌نام لغو شد.")
        return ConversationHandler.END
    
    event = db.get(Event, context.user_data["reg_event_id"])
    text = f"""
لطفاً مبلغ <b>{event.cost:,} تومان</b> را به کارت زیر واریز کنید:

<b>{BANK_CARD}</b>
{CARD_OWNER}

<b>بعد از واریز، فقط عکس رسید را اینجا ارسال کنید.</b>
(فایل یا متن قبول نیست)
"""
    await query.edit_message_text(text, parse_mode=ParseMode.HTML)
    return WAIT_RECEIPT

# دریافت رسید (فقط عکس)
async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("لطفاً فقط عکس رسید ارسال کنید! (فایل یا متن قبول نیست)")
        return WAIT_RECEIPT
    
    user_id = update.effective_user.id
    event_id = context.user_data["reg_event_id"]
    db = next(get_db())
    event = db.get(Event, event_id)
    user = db.query(User).filter(User.user_id == user_id).first()
    
    photo = update.message.photo[-1]
    caption = f"""
#رسید_پرداخت #{event.hashtag.replace('#','')}

نام: {user.full_name}
شماره دانشجویی: {user.student_id or 'مهمان'}
کد ملی: {user.national_code}
تلفن: {user.phone}

رویداد: {event.title}
مبلغ: {event.cost:,} تومان
زمان: {jdatetime.datetime.now().strftime('%Y/%m/%d - %H:%M')}
"""
    sent = await context.bot.send_photo(
        OPERATORS_GROUP,
        photo.file_id,
        caption=caption,
        parse_mode=ParseMode.HTML
    )
    
    await context.bot.send_message(
        OPERATORS_GROUP,
        "وضعیت رسید:",
        reply_to_message_id=sent.message_id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید", callback_data=f"receipt_ok_{sent.message_id}_{user_id}_{event_id}"),
             InlineKeyboardButton("ناخوانا", callback_data=f"receipt_blur_{sent.message_id}_{user_id}")],
            [InlineKeyboardButton("ابطال", callback_data=f"receipt_cancel_{sent.message_id}_{user_id}_{event_id}")]
        ])
    )
    
    await update.message.reply_text("رسید ارسال شد! منتظر تأیید اپراتورها باشید")
    
    # یادآوری و حذف خودکار
    context.job_queue.run_once(remind_payment, 3600, data={"user_id": user_id, "event_id": event_id})
    context.job_queue.run_once(cancel_unpaid, 7200, data={"user_id": user_id, "event_id": event_id})
    return ConversationHandler.END

async def remind_payment(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    await context.bot.send_message(data["user_id"], "یادآوری: هنوز رسید پرداختی ارسال نکردی. تا ۱ ساعت دیگر ثبت‌نامت منقضی میشه!")

async def cancel_unpaid(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    db = next(get_db())
    reg = db.query(Registration).filter(
        Registration.user_id == data["user_id"],
        Registration.event_id == data["event_id"],
        Registration.payment_status == "pending"
    ).first()
    if reg:
        db.delete(reg)
        event = db.get(Event, data["event_id"])
        event.auxiliary_capacity += 1
        db.commit()
        await context.bot.send_message(data["user_id"], "متأسفیم، به دلیل عدم ارسال رسید، ثبت‌نامت لغو شد.")

# تأیید/ناخوانا/ابطال توسط ادمین
async def handle_receipt_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("_")
    action = data[0] + "_" + data[1]  # receipt_ok یا receipt_blur یا receipt_cancel
    msg_id = int(data[2])
    user_id = int(data[3])
    
    db = next(get_db())
    
    if action == "receipt_ok":
        event_id = int(data[4])
        event = db.get(Event, event_id)
        user = db.query(User).filter(User.user_id == user_id).first()
        row = db.query(Registration).filter(Registration.event_id == event_id).count() + 1
        
        reg = Registration(event_id=event_id, user_id=user_id, row_number=row, payment_status="confirmed")
        db.add(reg)
        if event.capacity > 0:
            event.remaining_capacity -= 1
        db.commit()
        
        await context.bot.send_message(user_id, "پرداخت شما تأیید شد! ثبت‌نام با موفقیت انجام شد")
        await query.edit_message_text(query.message.text + f"\n\nتأیید شد توسط {query.from_user.first_name}")
        
        await context.bot.send_message(
            OPERATORS_GROUP,
            f"#ثبت_نام_تأییدشده #{event.hashtag.replace('#','')}\nردیف: {row}\nنام: {user.full_name}\nتلفن: {user.phone}"
        )
        
    elif action == "receipt_blur":
        await context.bot.send_message(user_id, "رسید شما ناخوانا بود. لطفاً رسید واضح‌تری ارسال کنید.")
        await query.edit_message_text(query.message.text + f"\n\nناخوانا — کاربر مطلع شد")
        
    elif action == "receipt_cancel":
        event_id = int(data[4])
        event = db.get(Event, event_id)
        event.auxiliary_capacity += 1
        db.commit()
        await context.bot.send_message(user_id, "رسید شما تأیید نشد. ثبت‌نام لغو شد.")
        await query.edit_message_text(query.message.text + f"\n\nابطال شد توسط {query.from_user.first_name}")

# ConversationHandler ثبت‌نام
event_reg_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_registration, pattern="^event_reg_")],
    states={
        REG_CONFIRM: [CallbackQueryHandler(confirm_paid_reg, pattern="^(reg_yes|reg_no)$")],
        WAIT_RECEIPT: [MessageHandler(filters.PHOTO, receive_receipt)]
    },
    fallbacks=[]
)

# هندلر دکمه‌های رسید
receipt_handler = CallbackQueryHandler(handle_receipt_action, pattern="^receipt_(ok|blur|cancel)_")
