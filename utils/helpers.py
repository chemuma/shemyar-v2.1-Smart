import jdatetime
from telegram import User as TGUser

def format_phone(phone: str) -> str:
    phone = phone.replace("+98", "0").replace("98", "0").lstrip("0")
    if phone.startswith("9") and len(phone) == 10:
        phone = "0" + phone
    return phone

def get_first_name(user: TGUser) -> str:
    return (user.full_name or user.first_name or "کاربر").split()[0]
