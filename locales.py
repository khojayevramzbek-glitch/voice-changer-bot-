"""
Multi-language localization strings for Voice Changer Bot.
Supported: Uzbek (uz), Russian (ru), English (en)
"""

LOCALES = {
    "uz": {
        "start_title": "👋 <b>Assalomu alaykum, {name}!</b>",
        "start_desc": (
            "🎙 <b>Voice Changer & TTS AI Bot</b>ga xush kelibsiz!\n\n"
            "Men siz yuborgan har qanday <b>ovozli xabar (voice)</b> yoki matnni 20+ xil qiziqarli effektlarga aylantirib beraman!\n\n"
            "✨ <b>Imkoniyatlarim:</b>\n"
            "• 🎭 <b>20+ Ovoz Effektlari:</b> Chipmunk, Robot, Alien, Monster, Geliy, Arvoh va h.k.\n"
            "• ✍️ <b>Text-to-Speech:</b> Yozgan matningizni turli ovozlarda o'qitish!\n"
            "• 🌧 <b>Fon Tovushlari:</b> Yomg'ir, Dengiz, Kamin, Bo'ron atmosferasi\n"
            "• 🌐 <b>Inline Mode:</b> Istalgan guruhda <code>@voicechangerautobot [matn]</code> deb ishlatish!\n\n"
            "👇 <b>Boshlash uchun:</b> Menga shunchaki <b>ovozli xabar</b> yoki <b>matn</b> yuboring!"
        ),
        "help_title": "ℹ️ <b>Botdan foydalanish bo'yicha qo'llanma:</b>",
        "help_text": (
            "1. <b>Ovozni o'zgartirish:</b> Menga ovozli xabar (voice) yuboring va chiqqan tugmalardan effekt tanlang.\n"
            "2. <b>Matndan ovoz yasash:</b> Menga istalgan matn yozib yuboring (masalan: <i>Salom do'stlar</i>) va kerakli ovoz effektini bosing.\n"
            "3. <b>Inline rejim:</b> Har qanday chatda <code>@voicechangerautobot [matn]</code> deb yozing va tayyor ovozli xabarni yuboring!\n"
            "4. <b>Fon tovushi qo'shish:</b> Ovoz yuborganingizdan so'ng '🌧 Fon tovushlari' bo'limidan yomg'ir, dengiz va h.k. qo'shing."
        ),
        "btn_effects": "🎭 Ovoz Effektlari",
        "btn_tts": "✍️ Matndan Ovozga (TTS)",
        "btn_ambience": "🌧 Fon Tovushlari",
        "btn_lang": "🌐 Tilni O'zgartirish",
        "btn_help": "ℹ️ Yordam",
        "btn_cancel": "🗑 Bekor qilish",
        "btn_back": "⬅️ Orqaga",
        "btn_another": "🎭 Boshqa effekt tanlash",
        "btn_add_ambience": "🌧 Fon qo'shish",
        "voice_received": "📥 <i>Ovozli xabar qabul qilindi, yuklab olinmoqda...</i>",
        "voice_ready": "✨ <b>Ovoz tayyor!</b> Kerakli effektni tanlang:",
        "ambience_ready": "🌧 <b>Fon tovushini tanlang:</b>",
        "text_received": "✍️ <b>Matn qabul qilindi!</b>\n\nQaysi ovozda o'qib beray?",
        "processing_effect": "⚙️ <b>{name}</b> effekti qo'llanmoqda... Iltimos kuting...",
        "processing_tts": "🎙 <b>{name}</b> ovozida nutq yaratilmoqda... Iltimos kuting...",
        "error_processing": "❌ Effektni qo'llashda xatolik yuz berdi.",
        "lang_choose": "🌐 <b>Iltimos, tilni tanlang / Пожалуйста, выберите язык / Choose language:</b>",
        "lang_changed": "✅ Til muvaffaqiyatli <b>O'zbekcha</b>ga o'zgartirildi!",
        "expired": "⚠️ Bu xabar muddati tugagan. Yangi ovoz yoki matn yuboring.",
        "cancelled": "❌ Bekor qilindi."
    },
    "ru": {
        "start_title": "👋 <b>Здравствуйте, {name}!</b>",
        "start_desc": (
            "🎙 Добро пожаловать в <b>Voice Changer & TTS AI Bot</b>!\n\n"
            "Я превращаю ваши <b>голосовые сообщения (voice)</b> и текст в 20+ забавных и крутых голосовых эффектов!\n\n"
            "✨ <b>Возможности:</b>\n"
            "• 🎭 <b>20+ Эффектов:</b> Бурундук, Робот, Пришелец, Монстр, Гелий, Призрак и др.\n"
            "• ✍️ <b>Text-to-Speech:</b> Озвучка любого текста разными голосами!\n"
            "• 🌧 <b>Фоновые звуки:</b> Дождь, Шум моря, Костер, Буря\n"
            "• 🌐 <b>Inline Режим:</b> Используйте прямо в группах <code>@voicechangerautobot [текст]</code>!\n\n"
            "👇 <b>Чтобы начать:</b> Отправьте мне <b>голосовое сообщение</b> или <b>текст</b>!"
        ),
        "help_title": "ℹ️ <b>Руководство пользователя:</b>",
        "help_text": (
            "1. <b>Изменение голоса:</b> Отправьте голосовое сообщение и выберите эффект кнопками.\n"
            "2. <b>Озвучка текста:</b> Напишите любой текст и выберите желаемый голос.\n"
            "3. <b>Инлайн режим:</b> В любом чате напишите <code>@voicechangerautobot [текст]</code> и отправьте готовое голосовое!\n"
            "4. <b>Фоновые звуки:</b> Добавляйте звуки дождя, моря к вашим сообщениям."
        ),
        "btn_effects": "🎭 Голосовые эффекты",
        "btn_tts": "✍️ Озвучка текста (TTS)",
        "btn_ambience": "🌧 Фоновые звуки",
        "btn_lang": "🌐 Сменить язык",
        "btn_help": "ℹ️ Помощь",
        "btn_cancel": "🗑 Отмена",
        "btn_back": "⬅️ Назад",
        "btn_another": "🎭 Выбрать другой эффект",
        "btn_add_ambience": "🌧 Добавить фон",
        "voice_received": "📥 <i>Голосовое сообщение получено, скачиваю...</i>",
        "voice_ready": "✨ <b>Голос готов!</b> Выберите желаемый эффект:",
        "ambience_ready": "🌧 <b>Выберите фоновый звук:</b>",
        "text_received": "✍️ <b>Текст получен!</b>\n\nКаким голосом озвучить?",
        "processing_effect": "⚙️ Применяется эффект <b>{name}</b>... Подождите...",
        "processing_tts": "🎙 Озвучивается голосом <b>{name}</b>... Подождите...",
        "error_processing": "❌ Ошибка при обработке аудио.",
        "lang_choose": "🌐 <b>Выберите язык / Choose language / Tilni tanlang:</b>",
        "lang_changed": "✅ Язык успешно изменен на <b>Русский</b>!",
        "expired": "⚠️ Срок действия этого аудио истек. Отправьте новое.",
        "cancelled": "❌ Отменено."
    },
    "en": {
        "start_title": "👋 <b>Hello, {name}!</b>",
        "start_desc": (
            "🎙 Welcome to <b>Voice Changer & TTS AI Bot</b>!\n\n"
            "I transform any <b>voice message</b> or text into 20+ awesome sound effects!\n\n"
            "✨ <b>Features:</b>\n"
            "• 🎭 <b>20+ Voice Effects:</b> Chipmunk, Robot, Alien, Monster, Helium, Ghost & more!\n"
            "• ✍️ <b>Text-to-Speech:</b> Speak any written text with unique character voices!\n"
            "• 🌧 <b>Atmospheric Sounds:</b> Rain, Ocean waves, Fireplace, Storm\n"
            "• 🌐 <b>Inline Mode:</b> Type <code>@voicechangerautobot [text]</code> in any chat!\n\n"
            "👇 <b>To start:</b> Simply send me a <b>voice message</b> or <b>text</b>!"
        ),
        "help_title": "ℹ️ <b>User Guide:</b>",
        "help_text": (
            "1. <b>Change Voice:</b> Send a voice note and pick an effect from the buttons.\n"
            "2. <b>Text to Speech:</b> Send any text message and choose an audio character voice.\n"
            "3. <b>Inline Mode:</b> In any chat, type <code>@voicechangerautobot [text]</code> to send instant voice notes!\n"
            "4. <b>Background Audio:</b> Mix atmospheric rain or ocean sounds behind your voice."
        ),
        "btn_effects": "🎭 Voice Effects",
        "btn_tts": "✍️ Text-to-Speech",
        "btn_ambience": "🌧 Background Sounds",
        "btn_lang": "🌐 Change Language",
        "btn_help": "ℹ️ Help",
        "btn_cancel": "🗑 Cancel",
        "btn_back": "⬅️ Back",
        "btn_another": "🎭 Try another effect",
        "btn_add_ambience": "🌧 Add background",
        "voice_received": "📥 <i>Voice message received, downloading...</i>",
        "voice_ready": "✨ <b>Voice ready!</b> Choose an effect below:",
        "ambience_ready": "🌧 <b>Choose background sound:</b>",
        "text_received": "✍️ <b>Text received!</b>\n\nWhich voice persona would you like to speak it?",
        "processing_effect": "⚙️ Applying <b>{name}</b> effect... Please wait...",
        "processing_tts": "🎙 Generating voice with <b>{name}</b>... Please wait...",
        "error_processing": "❌ Error processing audio.",
        "lang_choose": "🌐 <b>Choose your language / Tilni tanlang / Выберите язык:</b>",
        "lang_changed": "✅ Language successfully set to <b>English</b>!",
        "expired": "⚠️ This message has expired. Please send a new voice or text.",
        "cancelled": "❌ Cancelled."
    }
}

# User language storage in memory
USER_LANGUAGES = {}

def get_user_lang(user_id: int) -> str:
    """Returns the user's preferred language code (default 'uz')."""
    return USER_LANGUAGES.get(user_id, "uz")

def set_user_lang(user_id: int, lang_code: str):
    """Sets the user's preferred language."""
    if lang_code in LOCALES:
        USER_LANGUAGES[user_id] = lang_code

def t(user_id: int, key: str, **kwargs) -> str:
    """Translates a key into the user's language with format substitutions."""
    lang = get_user_lang(user_id)
    text = LOCALES.get(lang, LOCALES["uz"]).get(key, LOCALES["uz"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
