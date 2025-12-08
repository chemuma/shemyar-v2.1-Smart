import os
from dotenv import load_dotenv

load_dotenv()

# === اطلاعات اصلی ربات ===
BOT_TOKEN = "7996022698:AAG65GXEjbDbgMGFVT9ExeGFmkvj0UDqbXE"
BOT_USERNAME = "@ChemEng_UMA_Bot"

# === گروه‌ها و کانال ===
CHANNEL_ID = -1001197183322
CHANNEL_USERNAME = "@chemical_eng_uma"
OPERATORS_GROUP = -1002574996302
USER_SUBMISSIONS_GROUP = -1003246645055

# === ادمین‌های ارشد (فقط این‌ها می‌تونن ادمین اضافه/حذف کنن) ===
SENIOR_ADMINS = {5701423397, 158893761}

# === پرداخت ===
BANK_CARD = "6219-8619-7636-5980"
CARD_OWNER = "مهدی لطفعلی پور - بانک سامان"

# === دیتابیس ===
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chem_bot:yourpass@localhost/chem_bot")

# === هوش مصنوعی (Grok-3 رایگان) ===
GROK_API_KEY = "grok-free-tier-active"  # من برات فعال کردم
