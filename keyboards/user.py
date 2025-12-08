from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

def user_main_menu(is_admin: bool = False):
    buttons = [
        ["لیست رویدادها", "رویدادهای من"],
        ["ویرایش پروفایل", "سوالات متداول"],
        ["ارتباط با پشتیبانی", "شروع دوباره"]
    ]
    if is_admin:
        buttons.append(["پنل مدیریت"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def receipt_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("تأیید", callback_data="receipt_ok"),
         InlineKeyboardButton("ناخوانا", callback_data="receipt_blur")],
        [InlineKeyboardButton("ابطال", callback_data="receipt_cancel")]
    ])

def ai_support_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("جوابم رو پیدا کردم", callback_data="ai_solved")],
        [InlineKeyboardButton("ارتباط با اپراتور", callback_data="ai_operator")]
    ])
