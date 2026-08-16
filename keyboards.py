from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from audio_processor import VOICE_EFFECTS

def get_voice_effects_keyboard(file_token: str) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard with 2 columns of voice effect buttons.
    Callback data format: "fx:{effect_key}:{file_token}"
    """
    buttons = []
    row = []

    for key, effect in VOICE_EFFECTS.items():
        btn = InlineKeyboardButton(
            text=effect["name"],
            callback_data=f"fx:{key}:{file_token}"
        )
        row.append(btn)
        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Add quick action buttons at the bottom
    buttons.append([
        InlineKeyboardButton(text="❓ Effektlar haqida", callback_data="info:effects"),
        InlineKeyboardButton(text="🗑 Bekor qilish", callback_data=f"cancel:{file_token}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_effect_keyboard(file_token: str) -> InlineKeyboardMarkup:
    """Keyboard shown under converted voice note to allow converting again or trying other filters."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎭 Boshqa effekt tanlash", callback_data=f"menu:{file_token}"),
            ]
        ]
    )
