import re

def validate_persian_name(name: str) -> bool:
    name = name.strip()
    if len(name) < 6 or "  " in name or not re.search(r"[آ-ی]\s+[آ-ی]", name):
        return False
    if re.search(r"\d", name):
        return False
    return True

def validate_national_code(code: str) -> bool:
    if not re.match(r"^\d{10}$", code):
        return False
    check = int(code[9])
    total = sum(int(code[i]) * (10 - i) for i in range(9)) % 11
    return (total < 2 and check == total) or (total >= 2 and check == 11 - total)

def validate_student_id(sid: str) -> str:
    sid = sid.strip()
    if sid.startswith("44") and len(sid) >= 10:
        return "uma_student"
    if sid.startswith("444") and len(sid) >= 10:
        return "chem_student"
    if sid == "00":
        return "guest"
    return "invalid"
