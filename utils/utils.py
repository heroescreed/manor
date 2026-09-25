from constants import COLORS

def color_message(message: str, color: str = COLORS["default"]):
    color = COLORS.get(color, COLORS["default"])
    return color + message + "\033[0m"