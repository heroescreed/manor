import re

from discord.ext import commands
from constants import COLORS, committee_role

def color_message(message: str, color: str = COLORS["default"]):
    color = COLORS.get(color, COLORS["default"])
    return color + message + "\033[0m"

def check_student_number(student_number: str) -> bool:
    print(f"Checking student number: {student_number}")
    if len(student_number) != 9:
        return False
    return bool(re.match(r"^\d{9}$", student_number))

def is_committee_member(ctx: commands.Context) -> bool:
    return committee_role in [role.id for role in ctx.author.roles] # type: ignore