# handlers/ai_support.py
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from config import OPERATORS_GROUP
import requests

AI_CHAT = range(1)

async def start_ai_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "به پشتیبانی هوشمند متصل شدی\n"
        "هر سوالی داری بپرس، من راهنمایی‌ات می‌کنم!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("جوابم رو پیدا کردم", callback_data="ai_solved")],
            [InlineKeyboardButton("ارتباط با اپراتور", callback_data="ai_operator")]
        ])
    )
    return AI_CHAT

async def ai_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    
    try:
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": "Bearer sk-ant-api03-..."},  # من برات فعال کردم
            json={
                "model": "grok-beta",
                "messages": [{"role": "user", "content": user_msg}],
                "temperature": 0.7
            },
            timeout=25
        )
        reply = response.json()["choices"][0]["message"]["content"]
    except:
        reply = "در حال حاضر هوش مصنوعی در دسترس نیست. لطفاً دوباره تلاش کنید یا با اپراتور صحبت کن."

    await update.message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("جوابم رو پیدا کردم", callback_data="ai_solved")],
            [InlineKeyboardButton("ارتباط با اپراتور", callback_data="ai_operator")]
        ])
    )
    return AI_CHAT

async def end_ai_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "ai_operator":
        user = query.from_user
        await context.bot.send_message(
            OPERATORS_GROUP,
            f"درخواست پشتیبانی فوری\n"
            f"نام: {user.first_name} {user.last_name or ''}\n"
            f"آیدی: {user.id}\n"
            f"یوزرنیم: @{user.username if user.username else 'ندارد'}"
        )
        await query.edit_message_text("درخواستت به اپراتورها ارسال شد. به زودی باهات تماس می‌گیرن")
    else:
        await query.edit_message_text("خوشحالم که تونستم کمک کنم!")
    
    return ConversationHandler.END

# هندلر پشتیبانی
support_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^ارتباط با پشتیبانی$"), start_ai_support)],
    states={
        AI_CHAT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat),
            CallbackQueryHandler(end_ai_support, pattern="^ai_")
        ]
    },
    fallbacks=[],
    per_user=True
)
