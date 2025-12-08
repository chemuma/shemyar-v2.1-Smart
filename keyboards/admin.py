from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("ثبت رویداد جدید", callback_data="admin_new_event")],
        [InlineKeyboardButton("ویرایش رویداد", callback_data="admin_edit_event"),
         InlineKeyboardButton("فعال/غیرفعال", callback_data="admin_toggle_event")],
        [InlineKeyboardButton("اضافه دستی ثبت‌نام", callback_data="admin_manual_reg")],
        [InlineKeyboardButton("ارسال فرم نظرسنجی", callback_data="admin_send_survey")],
        [InlineKeyboardButton("اعلان عمومی", callback_data="admin_broadcast")],
        [InlineKeyboardButton("گزارش‌گیری", callback_data="admin_reports")],
        [InlineKeyboardButton("بلاک لیست", callback_data="admin_blocklist")],
        [InlineKeyboardButton("مدیریت ادمین‌ها", callback_data="admin_manage_admins")],
        [InlineKeyboardButton("برگشت به منوی کاربر", callback_data="back_to_user")]
    ])
