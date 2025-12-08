# main.py
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.start import start_conv
from handlers.events import show_events, event_reg_conv, receipt_handler
from handlers.admin import new_event_conv, enter_admin_panel
from handlers.admin_tools import admin_tools_conv, restart_bot
from handlers.ai_support import support_conv
from config import BOT_TOKEN
from database.db import get_db
from database.models import Event
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import jdatetime
from datetime import datetime

async def send_event_reminders(context):
    db = next(get_db())
    today = jdatetime.date.today()
    tomorrow = today + jdatetime.timedelta(days=1)
    tomorrow_str = tomorrow.strftime("%Y/%m/%d")
    
    events = db.query(Event).filter(Event.status == "active", Event.date_shamsi == tomorrow_str).all()
    for event in events:
        regs = db.query(Event.registrations).filter_by(event_id=event.id).all()
        for reg in regs:
            user = reg.user
            first_name = user.full_name.split()[0]
            text = f"""
{first_name} عزیز،
یادت نره!
فردا منتظرتیم

رویداد: {event.title}
تاریخ: {event.date_shamsi}

ساعت دقیق و جزئیات در کانال انجمن:
@chemical_eng_uma

حتما بیا، جاتو خالی نزاری 😅!
"""
            try:
                await context.bot.send_message(reg.user_id, text)
            except:
                pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # هندلرها
    app.add_handler(start_conv)
    app.add_handler(event_reg_conv)
    app.add_handler(receipt_handler)
    app.add_handler(new_event_conv)
    app.add_handler(admin_tools_conv)
    app.add_handler(support_conv)
    
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("لطفاً /start بزن")))
    app.add_handler(MessageHandler(filters.Regex("^لیست رویدادها$"), show_events))
    app.add_handler(MessageHandler(filters.Regex("^شروع دوباره$"), restart_bot))
    app.add_handler(CallbackQueryHandler(enter_admin_panel, pattern="^admin_panel$"))

    # یادآوری رویداد
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_event_reminders, 'cron', hour=18, minute=0, args=(app,))
    scheduler.start()

    print("ربات انجمن مهندسی شیمی محقق اردبیلی با موفقیت فعال شد!")
    app.run_polling()

if __name__ == "__main__":
    main()
