from openpyxl import Workbook
from io import BytesIO

def create_registration_excel(registrations, users_dict, event_title):
    wb = Workbook()
    ws = wb.active
    ws.title = "ثبت‌نام‌ها"
    ws.append(["ردیف", "نام کامل", "کد ملی", "شماره دانشجویی", "تلفن", "وضعیت پرداخت"])
    
    for reg in registrations:
        user = users_dict.get(reg.user_id)
        if user:
            status = "تأیید شده" if reg.payment_status == "confirmed" else "در انتظار"
            ws.append([
                reg.row_number,
                user.full_name,
                user.national_code,
                user.student_id or "مهمان",
                user.phone,
                status
            ])
    
    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio, f"گزارش_{event_title.replace(' ', '_')}.xlsx"
