from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from audio_processor import VOICE_EFFECTS, AMBIENCE_EFFECTS, TTS_VOICES
from locales import get_user_lang, t

def get_main_menu_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Bottom persistent menu for quick navigation."""
    lang = get_user_lang(user_id)
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(user_id, "btn_tts")),
                KeyboardButton(text=t(user_id, "btn_ambience"))
            ],
            [
                KeyboardButton(text=t(user_id, "btn_lang")),
                KeyboardButton(text=t(user_id, "btn_help"))
            ]
        ],
        resize_keyboard=True
    )


def get_voice_effects_keyboard(file_token: str, user_id: int, page: int = 1) -> InlineKeyboardMarkup:
    """
    Paginated inline keyboard for 18+ voice effects (8 per page for sleek mobile layout).
    """
    lang = get_user_lang(user_id)
    items_per_page = 8
    all_keys = list(VOICE_EFFECTS.keys())
    total_pages = (len(all_keys) + items_per_page - 1) // items_per_page

    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * items_per_page
    page_keys = all_keys[start_idx:start_idx + items_per_page]

    buttons = []
    row = []

    for key in page_keys:
        effect = VOICE_EFFECTS[key]
        name = effect.get(lang, effect.get("uz"))
        row.append(InlineKeyboardButton(text=name, callback_data=f"fx:{key}:{file_token}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Navigation buttons (only if multiple pages exist)
    if total_pages > 1:
        nav_row = []
        if page > 1:
            nav_row.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data=f"page:{page-1}:{file_token}"))
        nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
        if page < total_pages:
            nav_row.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data=f"page:{page+1}:{file_token}"))
        buttons.append(nav_row)

    # Ambience and cancel
    buttons.append([
        InlineKeyboardButton(text=t(user_id, "btn_ambience"), callback_data=f"menu_amb:{file_token}"),
        InlineKeyboardButton(text=t(user_id, "btn_cancel"), callback_data=f"cancel:{file_token}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_ambience_keyboard(file_token: str, user_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for atmospheric background sound mixing."""
    lang = get_user_lang(user_id)
    buttons = []
    row = []

    for key, amb in AMBIENCE_EFFECTS.items():
        name = amb.get(lang, amb.get("uz"))
        row.append(InlineKeyboardButton(text=name, callback_data=f"amb:{key}:{file_token}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(text=t(user_id, "btn_back"), callback_data=f"menu:{file_token}"),
        InlineKeyboardButton(text=t(user_id, "btn_cancel"), callback_data=f"cancel:{file_token}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_tts_keyboard(text_token: str, user_id: int) -> InlineKeyboardMarkup:
    """Inline keyboard for choosing TTS reader voice persona."""
    buttons = []
    for key, v in TTS_VOICES.items():
        buttons.append([
            InlineKeyboardButton(text=v["name"], callback_data=f"tts:{key}:{text_token}")
        ])

    buttons.append([
        InlineKeyboardButton(text=t(user_id, "btn_cancel"), callback_data=f"cancel:{text_token}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_after_effect_keyboard(file_token: str, user_id: int) -> InlineKeyboardMarkup:
    """Keyboard shown under a converted voice message."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(user_id, "btn_another"), callback_data=f"menu:{file_token}"),
                InlineKeyboardButton(text=t(user_id, "btn_add_ambience"), callback_data=f"menu_amb:{file_token}")
            ]
        ]
    )


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Language selection keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang:en")
            ]
        ]
    )
