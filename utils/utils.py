import re

from constants import COLORS

def color_message(message: str, color: str = COLORS["default"]):
    color = COLORS.get(color, COLORS["default"])
    return color + message + "\033[0m"

def check_student_number(student_number: str) -> bool:
    print(f"Checking student number: {student_number}")
    if len(student_number) != 9:
        return False
    return bool(re.match(r"^\d{9}$", student_number))