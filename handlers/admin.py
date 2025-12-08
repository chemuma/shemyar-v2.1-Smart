# handlers/admin.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler, MessageHandler, filters
from database.db import get_db
from database.models import Event, User
from config import SENIOR_ADMINS
import jdatetime
import re

# استیت‌های ثبت رویداد جدید
(
    NEW_EVENT_TYPE, NEW_EVENT_TITLE, NEW_EVENT_DESC, NEW_EVENT_DATE,
    NEW_EVENT_LOCATION, NEW_EVENT_COST, NEW_EVENT_CAPACITY, NEW_EVENT_PREVIEW
) = range(8)

async def enter_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    db = next(get_db())
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not (user and (user.is_admin or user_id in SENIOR_ADMINS)):
        await query.edit_message_text("شما دسترسی به پنل مدیریت ندارید.")
        return ConversationHandler.END

    from keyboards.admin import admin_main_menu
    await query.edit_message_text(
        "به پنل مدیریت خوش آمدید\nچه کاری می‌خواهید انجام دهید؟",
        reply_markup=admin_main_menu()
    )
    return ConversationHandler.END

async def start_new_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("دوره آموزشی", callback_data="type_دوره")],
        [InlineKeyboardButton("بازدید علمی", callback_data="type_بازدید")],
        [InlineKeyboardButton("گفتمان/کارگاه", callback_data="type_گفتمان")],
        [InlineKeyboardButton("لغو", callback_data="cancel_new_event")]
    ])
    await query.edit_message_text("لطفاً نوع رویداد را انتخاب کنید:", reply_markup=keyboard)
    return NEW_EVENT_TYPE

async def get_event_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_new_event":
        from keyboards.admin import admin_main_menu
        await query.edit_message_text("عملیات لغو شد.", reply_markup=admin_main_menu())
        return ConversationHandler.END
    
    context.user_data["event_type"] = query.data.replace("type_", "")
    await query.edit_message_text("عنوان رویداد را وارد کنید:\n(این عنوان نباید تکراری باشد)")
    return NEW_EVENT_TITLE

async def get_event_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    title = update.message.text.strip()
    db = next(get_db())
    if db.query(Event).filter(Event.title == title).first():
        await update.message.reply_text("این عنوان قبلاً استفاده شده! عنوان دیگری انتخاب کنید:")
        return NEW_EVENT_TITLE
    
    context.user_data["event_title"] = title
    await update.message.reply_text("توضیحات کامل رویداد را وارد کنید:\n(متن اعلان در کانال)")
    return NEW_EVENT_DESC

async def get_event_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["event_desc"] = update.message.text
    await update.message.reply_text("تاریخ برگزاری را به شمسی وارد کنید:\nمثال: ۱۴۰۴/۰۹/۲۰")
    return NEW_EVENT_DATE

async def get_event_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    date_text = update.message.text.strip()
    if not re.match(r"^\d{4}/\d{2}/\d{2}$", date_text):
        await update.message.reply_text("لطفاً فقط تاریخ رو به این فرمت وارد کن:\n۱۴۰۴/۰۹/۲۰")
        return NEW_EVENT_DATE
    
    context.user_data["event_date"] = date_text
    await update.message.reply_text("محل برگزاری را وارد کنید:")
    return NEW_EVENT_LOCATION

async def get_event_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["event_location"] = update.message.text
    await update.message.reply_text("هزینه شرکت در رویداد (به تومان):\nرایگان = ۰")
    return NEW_EVENT_COST

async def get_event_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", "").replace("تومان", "").replace("تومن", "")
    try:
        cost = int(text)
        if cost < 0:
            raise ValueError
    except:
        await update.message.reply_text("هزینه باید فقط عدد باشه (مثلاً 50000 یا 0)")
        return NEW_EVENT_COST
        
    context.user_data["event_cost"] = cost
    await update.message.reply_text("ظرفیت رویداد (۰ = نامحدود):")
    return NEW_EVENT_CAPACITY

async def get_event_capacity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cap = int(update.message.text.strip())
        if cap < 0:
            raise ValueError
    except:
        await update.message.reply_text("ظرفیت باید عدد باشد!")
        return NEW_EVENT_CAPACITY

    context.user_data["event_capacity"] = cap
    remaining = cap if cap > 0 else 999999
    aux = cap if cap > 0 else 999999
    
    # پیش‌نمایش
    preview = f"""
پیش‌نمایش رویداد

عنوان: {context.user_data['event_title']}
نوع: {context.user_data['event_type']}
توضیحات: {context.user_data['event_desc']}
تاریخ: {context.user_data['event_date']}
محل: {context.user_data['event_location']}
هزینه: {'رایگان' if context.user_data['event_cost'] == 0 else f'{context.user_data['event_cost']:,} تومان'}
ظرفیت: {'نامحدود' if cap == 0 else cap}

آیا اطلاعات درست است؟
    """
    await update.message.reply_text(
        preview,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تأیید و ثبت", callback_data="event_save")],
            [InlineKeyboardButton("لغو", callback_data="cancel_new_event")]
        ])
    )
    return NEW_EVENT_PREVIEW

async def save_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel_new_event":
        from keyboards.admin import admin_main_menu
        await query.edit_message_text("ثبت رویداد لغو شد.", reply_markup=admin_main_menu())
        return ConversationHandler.END

    db = next(get_db())
    
    cap = context.user_data["event_capacity"]
    hashtag = "#" + "".join(c for c in context.user_data["event_title"] if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")

    event = Event(
        title=context.user_data["event_title"],
        type=context.user_data["event_type"],
        description=context.user_data["event_desc"],
        date_shamsi=context.user_data["event_date"],
        location=context.user_data["event_location"],
        cost=context.user_data["event_cost"],
        capacity=cap,
        remaining_capacity=cap if cap > 0 else 999999,
        auxiliary_capacity=cap if cap > 0 else 999999,
        status="active",
        hashtag=hashtag
    )
    db.add(event)
    db.commit()

    # اعلان عمومی به همه کاربران
    users = db.query(User).all()
    announcement = f"""
یک #{context.user_data['event_type']} جدید اضافه شد!

{context.user_data['event_desc']}

تاریخ: {context.user_data['event_date']}
محل: {context.user_data['event_location']}
هزینه: {'رایگان' if event.cost == 0 else f'{event.cost:,} تومان'}

همین الان ثبت‌نام کن 
"""
    success_count = 0
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user.user_id,
                text=announcement,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("ثبت‌نام کن", callback_data=f"event_reg_{event.id}")
                ]])
            )
            success_count += 1
        except:
            pass

    from keyboards.admin import admin_main_menu
    await query.edit_message_text(
        f"رویداد با موفقیت ثبت شد!\n\n"
        f"عنوان: {event.title}\n"
        f"هشتگ: {event.hashtag}\n"
        f"اعلان به {success_count} نفر ارسال شد.",
        reply_markup=admin_main_menu()
    )
    context.user_data.clear()
    return ConversationHandler.END

# ConversationHandler ثبت رویداد
new_event_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_new_event, pattern="^admin_new_event$")],
    states={
        NEW_EVENT_TYPE: [CallbackQueryHandler(get_event_type)],
        NEW_EVENT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_title)],
        NEW_EVENT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_desc)],
        NEW_EVENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_date)],
        NEW_EVENT_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_location)],
        NEW_EVENT_COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_cost)],
        NEW_EVENT_CAPACITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_event_capacity)],
        NEW_EVENT_PREVIEW: [CallbackQueryHandler(save_event, pattern="^(event_save|cancel_new_event)$")],
    },
    fallbacks=[],
    per_user=False
)
