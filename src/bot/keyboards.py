from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config.buttons import (
    START_BUTTON,
    VIDEO_BUTTON,
    CAMERA_BUTTON,
    RESET_BUTTON,
    SEARCH_BUTTON,
    CONFIG_BUTTON,
    ACCURACY_BUTTON,
    BACK_BUTTON,
    FRAME_SKIP_BUTTON,
    SESSION_TIMEOUT_BUTTON,
    CAMERA_ROTATION_BUTTON,
    CAMERA_DURATION_BUTTON,
    STATUS_BUTTON,
    STATS_BUTTON,
    HELP_INLINE_BUTTON,
    ROTATION_OFF_BUTTON,
    ROTATION_90_BUTTON,
    ROTATION_180_BUTTON,
    ROTATION_270_BUTTON,
)


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """Get the main menu keyboard with a 3-row layout"""
    buttons = [
        [KeyboardButton(text=VIDEO_BUTTON), KeyboardButton(text=CAMERA_BUTTON)],
        [KeyboardButton(text=SEARCH_BUTTON), KeyboardButton(text=RESET_BUTTON)],
        [KeyboardButton(text=CONFIG_BUTTON)],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_back_keyboard() -> ReplyKeyboardMarkup:
    """Get a keyboard with just the back button"""
    buttons = [[KeyboardButton(text=BACK_BUTTON)]]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_config_keyboard() -> ReplyKeyboardMarkup:
    """Get the configuration menu keyboard"""
    buttons = [
        [KeyboardButton(text=ACCURACY_BUTTON)],
        [
            KeyboardButton(text=FRAME_SKIP_BUTTON),
            KeyboardButton(text=SESSION_TIMEOUT_BUTTON),
        ],
        [
            KeyboardButton(text=CAMERA_ROTATION_BUTTON),
            KeyboardButton(text=CAMERA_DURATION_BUTTON),
        ],
        [KeyboardButton(text=BACK_BUTTON)],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_help_inline_keyboard() -> InlineKeyboardMarkup:
    """Get an inline keyboard with command buttons for the help message"""
    buttons = [
        [
            InlineKeyboardButton(text=STATUS_BUTTON, callback_data="cmd_status"),
            InlineKeyboardButton(text=STATS_BUTTON, callback_data="cmd_stats"),
        ],
        [InlineKeyboardButton(text=HELP_INLINE_BUTTON, callback_data="cmd_start")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_rotation_inline_keyboard(current_value: str) -> InlineKeyboardMarkup:
    """Get an inline keyboard for selecting camera rotation"""
    buttons = [
        [
            InlineKeyboardButton(
                text=ROTATION_OFF_BUTTON, callback_data=f"rotation_off"
            ),
            InlineKeyboardButton(text=ROTATION_90_BUTTON, callback_data=f"rotation_90"),
        ],
        [
            InlineKeyboardButton(
                text=ROTATION_180_BUTTON, callback_data=f"rotation_180"
            ),
            InlineKeyboardButton(
                text=ROTATION_270_BUTTON, callback_data=f"rotation_270"
            ),
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)



