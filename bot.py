import asyncio
import logging
import sys
import uuid
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineQuery, InlineQueryResultArticle,
    InputTextMessageContent, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, LOG_BOT_TOKEN, ADMIN_ID, TEMP_DIR
from audio_processor import (
    apply_voice_effect, apply_ambience_effect, generate_tts,
    VOICE_EFFECTS, AMBIENCE_EFFECTS, TTS_VOICES
)
from locales import get_user_lang, set_user_lang, t
from keyboards import (
    get_main_menu_keyboard, get_voice_effects_keyboard,
    get_ambience_keyboard, get_tts_keyboard,
    get_after_effect_keyboard, get_language_keyboard
)
from database import (
    register_user, increment_voice, increment_tts,
    get_detailed_statistics, get_recent_users, get_all_user_ids,
    set_admin_id, get_admin_id, get_now_uz, UZ_TZ
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("VoiceChangerBot")

# In-memory storage for pending audio and text sessions
AUDIO_STORAGE: Dict[str, dict] = {}
TEXT_STORAGE: Dict[str, dict] = {}

MAIN_BOT_TOKEN = "8719968713:AAH8OeK7Y8LBwKx7KNmBM4VznlwCuFn3TBE"
HELPER_BOT_TOKEN = "8935735357:AAFsSTeoirZ5YAAVyGatSCrOn_eT5um2pnE"

main_bot = Bot(token=BOT_TOKEN or MAIN_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
log_bot = Bot(token=LOG_BOT_TOKEN or HELPER_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

dp = Dispatcher()
log_dp = Dispatcher()


def get_current_admin_id() -> Optional[int]:
    """Returns the effective admin ID from config or database."""
    if ADMIN_ID:
        return ADMIN_ID
    return get_admin_id()


async def send_to_log_bot(text: Optional[str] = None, voice_path: Optional[Path] = None, caption: Optional[str] = None):
    """Guaranteed sender to Log Bot with direct admin dispatch."""
    admin_id = get_current_admin_id()
    if not admin_id:
        return

    try:
        if text:
            await log_bot.send_message(chat_id=admin_id, text=text, parse_mode=ParseMode.HTML)
        if voice_path and voice_path.exists():
            v_file = FSInputFile(voice_path)
            await log_bot.send_voice(chat_id=admin_id, voice=v_file, caption=caption or "", parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error("Error dispatching to log_bot (admin_id=%s): %s", admin_id, e)


async def cleanup_old_files():
    """Periodically removes files and sessions older than 30 minutes."""
    while True:
        try:
            await asyncio.sleep(600)
            now = time.time()
            for storage in (AUDIO_STORAGE, TEXT_STORAGE):
                expired_tokens = []
                for token, data in list(storage.items()):
                    if now - data.get("created_at", now) > 1800:
                        expired_tokens.append(token)
                        if "path" in data and data["path"].exists():
                            try:
                                data["path"].unlink(missing_ok=True)
                            except Exception:
                                pass
                for token in expired_tokens:
                    storage.pop(token, None)
        except Exception as e:
            logger.error("Error in cleanup task: %s", e)


# ==================== LOG BOT HANDLERS & DASHBOARD ====================

def get_log_bot_inline_menu() -> InlineKeyboardMarkup:
    """Big clear inline buttons for Log Bot dashboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Jonli Statistika & Reyting", callback_data="log_stats")
            ],
            [
                InlineKeyboardButton(text="👥 Foydalanuvchilar Ro'yxati (15 ta)", callback_data="log_users")
            ],
            [
                InlineKeyboardButton(text="📢 Barchaga Xabar Yuborish", callback_data="log_broadcast_info")
            ]
        ]
    )


@log_dp.message(CommandStart())
async def log_cmd_start(message: Message):
    """Log bot start command with inline dashboard."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Xo'jayin"

    set_admin_id(user_id)
    text = (
        f"👑 <b>Assalomu alaykum, {name}!</b>\n\n"
        "🕵️‍♂️ <b>Sizning shaxsiy Admin & Log Botingiz tayyor!</b>\n\n"
        "Asosiy botdagi barcha yangi kirganlar, ovozlar va statistika shu yerda ko'rinadi.\n\n"
        "👇 <b>Kerakli bo'limni tanlang:</b>"
    )
    await message.answer(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)


@log_dp.callback_query(F.data == "log_stats")
@log_dp.message(Command("stats"))
@log_dp.message(F.text == "📊 Jonli Statistika")
async def log_show_stats_cb(event, bot: Bot):
    """Detailed live stats."""
    stats = get_detailed_statistics()

    top_text = ""
    if stats["top_effects"]:
        for idx, (fx_name, count) in enumerate(stats["top_effects"], 1):
            top_text += f"   {idx}. {fx_name} — <b>{count} marta</b>\n"
    else:
        top_text = "   <i>Hozircha ma'lumot yo'q</i>\n"

    uz_time = get_now_uz().strftime("%H:%M:%S (%d/%m/%Y)")
    text = (
        "📊 <b>BOTNING TO'LIQ STATISTIKASI VA METRIKALARI</b>\n\n"
        f"👥 <b>Jami /start bosganlar:</b> {stats['total_users']} ta foydalanuvchi\n"
        f"🟢 <b>Bugun faol bo'lganlar:</b> {stats['today_active']} ta\n"
        f"🎙 <b>Jami yuborilgan ovozlar:</b> {stats['total_voices']} ta\n"
        f"✍️ <b>Matndan o'qitilgan (TTS):</b> {stats['total_tts']} ta\n\n"
        "🔥 <b>Eng mashhur ovoz effektlari:</b>\n"
        f"{top_text}\n"
        f"🕒 <i>Yangilangan vaqt (Toshkent): {uz_time}</i>"
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)


@log_dp.callback_query(F.data == "log_users")
@log_dp.message(Command("users"))
@log_dp.message(F.text == "👥 Foydalanuvchilar Ro'yxati")
async def log_show_users_cb(event, bot: Bot):
    """Shows full list of recent users."""
    users = get_recent_users(15)
    if not users:
        msg = "👥 Hozircha foydalanuvchilar mavjud emas."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)
            await event.answer()
        else:
            await event.answer(msg, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)
        return

    text = "👥 <b>OXIRGI FOYDALANUVCHILAR RO'YXATI (15 ta):</b>\n\n"
    for idx, u in enumerate(users, 1):
        dt = datetime.fromtimestamp(u["last_active"], tz=UZ_TZ).strftime("%H:%M - %d/%m")
        u_name = u["first_name"] or "Ismsiz"
        u_tag = f"(@{u['username']})" if u["username"] else "(username yo'q)"
        text += (
            f"<b>{idx}. {u_name}</b> {u_tag}\n"
            f"   🆔 ID: <code>{u['user_id']}</code>\n"
            f"   🎙 Ovozlar: {u['voice_count']} ta | ✍️ TTS: {u['tts_count']} ta\n"
            f"   🕒 Oxirgi faollik: <i>{dt}</i>\n\n"
        )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)
        await event.answer()
    else:
        await event.answer(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)


@log_dp.callback_query(F.data == "log_broadcast_info")
async def log_broadcast_info_cb(callback: CallbackQuery):
    """Help for broadcast."""
    text = (
        "📢 <b>Barcha foydalanuvchilarga xabar tarqatish:</b>\n\n"
        "Shu botga quyidagi formatda xabar yozing:\n"
        "<code>/send Salom hammaga! Botda yangi Gollivud ovozlari chiqdi!</code>\n\n"
        "Bot asosiy botdagi barcha do'stlaringizga bu xabarni yetkazadi!"
    )
    await callback.message.edit_text(text, reply_markup=get_log_bot_inline_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()


@log_dp.message(Command("send"))
@log_dp.message(Command("broadcast"))
async def log_do_broadcast(message: Message):
    """Broadcast directly from Log Bot to all users of Main Bot!"""
    text_to_send = message.text.replace("/send", "", 1).replace("/broadcast", "", 1).strip()
    if not text_to_send:
        await message.reply("⚠️ Xabar matnini yozing!\nMisol: <code>/send Yangilik!</code>", parse_mode=ParseMode.HTML)
        return

    user_ids = get_all_user_ids()
    sent_count = 0
    status_msg = await message.reply(f"📤 {len(user_ids)} ta foydalanuvchiga yuborilmoqda...")

    for u_id in user_ids:
        try:
            await main_bot.send_message(chat_id=u_id, text=f"📢 <b>Admin Xabari:</b>\n\n{text_to_send}", parse_mode=ParseMode.HTML)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status_msg.edit_text(f"✅ Xabar <b>{sent_count} / {len(user_ids)}</b> ta foydalanuvchiga muvaffaqiyatli yetkazildi!", parse_mode=ParseMode.HTML)


# ==================== MAIN VOICE BOT HANDLERS ====================

@dp.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    """Main bot start command."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Do'stim"
    username = message.from_user.username if message.from_user else None

    if username and username.lower() == "khojayev_ramz":
        set_admin_id(user_id)

    is_new, _ = register_user(user_id, username, name)

    # Notify log bot
    if is_new and user_id != get_current_admin_id():
        u_tag = f"@{username}" if username else "username yo'q"
        await send_to_log_bot(
            text=(
                f"🔔 <b>YANGI FOYDALANUVCHI KIRDI!</b>\n\n"
                f"👤 <b>Ism:</b> {name}\n"
                f"🔗 <b>Username:</b> {u_tag}\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"🕒 <b>Vaqt (Toshkent):</b> {get_now_uz().strftime('%H:%M:%S (%d/%m/%Y)')}"
            )
        )

    if message.from_user and message.from_user.language_code:
        lang_code = message.from_user.language_code[:2].lower()
        if lang_code in ("ru", "en"):
            set_user_lang(user_id, lang_code)

    title = t(user_id, "start_title", name=name)
    desc = t(user_id, "start_desc")
    full_text = f"{title}\n\n{desc}"

    await message.answer(
        full_text,
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )


@dp.message(Command("help"))
@dp.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь", "ℹ️ Help"]))
async def cmd_help(message: Message):
    """Help handler."""
    user_id = message.from_user.id if message.from_user else 0
    title = t(user_id, "help_title")
    text = t(user_id, "help_text")
    await message.answer(f"{title}\n\n{text}", parse_mode=ParseMode.HTML)


@dp.message(Command("lang"))
@dp.message(F.text.in_(["🌐 Tilni O'zgartirish", "🌐 Сменить язык", "🌐 Change Language"]))
async def cmd_language(message: Message):
    """Language switcher."""
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        t(user_id, "lang_choose"),
        reply_markup=get_language_keyboard(),
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.in_(["✍️ Matndan Ovozga (TTS)", "✍️ Озвучка текста (TTS)", "✍️ Text-to-Speech"]))
async def cmd_tts_info(message: Message):
    user_id = message.from_user.id if message.from_user else 0
    msg = {
        "uz": "✍️ <b>Menga istalgan matn yozib yuboring!</b>\n\nMen uni tabiiy sun'iy intellekt ovozida o'qib, turli qiziqarli effektlarga aylantirib beraman.",
        "ru": "✍️ <b>Напишите мне любой текст!</b>\n\nЯ озвучу его красивым голосом и предложу классные эффекты.",
        "en": "✍️ <b>Send me any text message!</b>\n\nI will generate realistic speech and apply fun sound effects to it."
    }
    lang = get_user_lang(user_id)
    await message.answer(msg.get(lang, msg["uz"]), parse_mode=ParseMode.HTML)


@dp.message(F.text.in_(["🌧 Fon Tovushlari", "🌧 Фоновые звуки", "🌧 Background Sounds"]))
async def cmd_ambience_info(message: Message):
    user_id = message.from_user.id if message.from_user else 0
    msg = {
        "uz": "🌧 <b>Fon tovushlarini qo'shish uchun:</b>\nAvval menga ovozli xabar (voice) yuboring, so'ng '🌧 Fon tovushlari' tugmasini bosing!",
        "ru": "🌧 <b>Чтобы добавить фоновые звуки:</b>\nСначала отправьте голосовое сообщение, затем выберите '🌧 Фоновые звуки'!",
        "en": "🌧 <b>To mix background sounds:</b>\nSend a voice note first, then select '🌧 Background Sounds'!"
    }
    lang = get_user_lang(user_id)
    await message.answer(msg.get(lang, msg["uz"]), parse_mode=ParseMode.HTML)


# ---------------------- VOICE & AUDIO HANDLER ----------------------

@dp.message(F.voice | F.audio | F.video_note)
async def handle_incoming_voice(message: Message, bot: Bot):
    """Downloads incoming voice/audio."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    username = message.from_user.username
    file_token = uuid.uuid4().hex[:10]

    register_user(user_id, username, name)
    status_msg = await message.reply(t(user_id, "voice_received"), parse_mode=ParseMode.HTML)

    try:
        if message.voice:
            file_id = message.voice.file_id
            ext = ".ogg"
            media_type = "🎙 Ovozli xabar"
        elif message.audio:
            file_id = message.audio.file_id
            ext = ".mp3"
            media_type = "🎵 Audio fayl"
        else:
            file_id = message.video_note.file_id
            ext = ".mp4"
            media_type = "📹 Video xabar"

        file = await bot.get_file(file_id)
        if not file.file_path:
            await status_msg.edit_text(t(user_id, "error_processing"))
            return

        dest_path = TEMP_DIR / f"{file_token}_input{ext}"
        await bot.download_file(file.file_path, destination=dest_path)

        AUDIO_STORAGE[file_token] = {
            "path": dest_path,
            "user_id": user_id,
            "created_at": time.time(),
            "first_name": name,
            "username": username
        }

        # Send original audio to Helper Log Bot in background (non-blocking!)
        u_tag = f"@{username}" if username else "yo'q"
        asyncio.create_task(send_to_log_bot(
            voice_path=dest_path,
            caption=(
                f"📥 <b>YANGI ASL OVOZ KELDI!</b>\n\n"
                f"👤 <b>Kimdan:</b> {name} ({u_tag})\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"📂 <b>Turi:</b> {media_type}\n"
                f"🕒 <b>Vaqt:</b> {get_now_uz().strftime('%H:%M:%S')}"
            )
        ))

        keyboard = get_voice_effects_keyboard(file_token, user_id, page=1)
        await status_msg.edit_text(
            t(user_id, "voice_ready"),
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.exception("Error downloading audio: %s", e)
        await status_msg.edit_text(t(user_id, "error_processing"))


# ---------------------- TEXT TO SPEECH HANDLER ----------------------

@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text_input(message: Message):
    """Handles text input."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    username = message.from_user.username
    text_content = message.text.strip()

    register_user(user_id, username, name)

    if len(text_content) > 500:
        await message.reply("⚠️ Matn juda uzun. Iltimos, 500 belgidan oshmagan matn yuboring.")
        return

    text_token = uuid.uuid4().hex[:10]
    TEXT_STORAGE[text_token] = {
        "text": text_content,
        "user_id": user_id,
        "created_at": time.time(),
        "first_name": name,
        "username": username
    }

    u_tag = f"@{username}" if username else "yo'q"
    asyncio.create_task(send_to_log_bot(
        text=(
            f"✍️ <b>MATN YOZILDI (TTS):</b>\n\n"
            f"👤 <b>Kimdan:</b> {name} ({u_tag})\n"
            f"📝 <b>Matn:</b> «<i>{text_content}</i>»"
        )
    ))

    keyboard = get_tts_keyboard(text_token, user_id)
    await message.reply(
        f"✍️ <i>«{text_content[:60]}...»</i>\n\n{t(user_id, 'text_received')}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# ---------------------- CALLBACK QUERY HANDLERS ----------------------

@dp.callback_query(F.data.startswith("setlang:"))
async def handle_set_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]
    set_user_lang(user_id, lang_code)

    await callback.message.edit_text(t(user_id, "lang_changed"), parse_mode=ParseMode.HTML)
    await callback.message.answer(t(user_id, "start_desc"), reply_markup=get_main_menu_keyboard(user_id), parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    page = int(parts[1])
    file_token = parts[2]

    keyboard = get_voice_effects_keyboard(file_token, user_id, page=page)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@dp.callback_query(F.data.startswith("fx:"))
async def handle_effect_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    parts = callback.data.split(":")
    effect_key, file_token = parts[1], parts[2]

    effect = VOICE_EFFECTS.get(effect_key)
    if not effect:
        await callback.answer("Effekt topilmadi.", show_alert=True)
        return

    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    effect_name = effect.get(lang, effect.get("uz"))
    desc = effect.get(f"desc_{lang}", effect.get("desc_uz"))

    await callback.answer(f"⏳ {effect_name}...")
    output_path = TEMP_DIR / f"{file_token}_{effect_key}.ogg"

    try:
        success = await apply_voice_effect(data["path"], output_path, effect_key)
        if not success or not output_path.exists():
            await callback.message.reply(t(user_id, "error_processing"))
            return

        increment_voice(user_id, effect_name)

        caption = f"✨ <b>Effekt:</b> {effect_name}\n📝 <i>{desc}</i>\n\n🤖 @voicechangerautobot"

        # Reply to user IMMEDIATELY!
        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_after_effect_keyboard(file_token, user_id)
        )

        # Log in background without blocking user!
        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        asyncio.create_task(send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"✨ <b>O'ZGARTIRILGAN OVOZ!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"🎭 <b>Tanlangan Effekt:</b> {effect_name}"
            )
        ))
    except Exception as e:
        logger.exception("Error in voice effect: %s", e)
        await callback.message.reply(t(user_id, "error_processing"))


@dp.callback_query(F.data.startswith("amb:"))
async def handle_ambience_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    parts = callback.data.split(":")
    amb_key, file_token = parts[1], parts[2]

    amb = AMBIENCE_EFFECTS.get(amb_key)
    if not amb:
        await callback.answer("Fon topilmadi.", show_alert=True)
        return

    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    amb_name = amb.get(lang, amb.get("uz"))
    await callback.answer(f"⏳ {amb_name}...")
    output_path = TEMP_DIR / f"{file_token}_{amb_key}.ogg"

    try:
        success = await apply_ambience_effect(data["path"], output_path, amb_key)
        if not success or not output_path.exists():
            await callback.message.reply(t(user_id, "error_processing"))
            return

        increment_voice(user_id, f"Fon: {amb_name}")
        caption = f"🌧 <b>Fon:</b> {amb_name}\n\n🤖 @voicechangerautobot"

        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_after_effect_keyboard(file_token, user_id)
        )

        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        asyncio.create_task(send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"🌧 <b>FON QO'SHILGAN OVOZ!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"🌧 <b>Tanlangan Fon:</b> {amb_name}"
            )
        ))
    except Exception as e:
        logger.exception("Error in ambience effect: %s", e)
        await callback.message.reply(t(user_id, "error_processing"))


@dp.callback_query(F.data.startswith("tts:"))
async def handle_tts_callback(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    voice_key, text_token = parts[1], parts[2]

    data = TEXT_STORAGE.get(text_token)
    if not data:
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    voice_info = TTS_VOICES.get(voice_key, TTS_VOICES["uz_female"])
    await callback.answer("🎙 Nutq tayyorlanmoqda...")

    file_token = uuid.uuid4().hex[:10]
    output_path = TEMP_DIR / f"{file_token}_tts.ogg"

    try:
        success = await generate_tts(data["text"], voice_key, output_path)
        if not success or not output_path.exists():
            await callback.message.reply(t(user_id, "error_processing"))
            return

        increment_tts(user_id, voice_info["name"])

        AUDIO_STORAGE[file_token] = {
            "path": output_path,
            "user_id": user_id,
            "created_at": time.time(),
            "first_name": data.get("first_name", "Foydalanuvchi"),
            "username": data.get("username")
        }

        caption = (
            f"✍️ <i>«{data['text'][:80]}»</i>\n\n"
            f"🗣 <b>Ovoz:</b> {voice_info['name']}\n"
            f"🤖 @voicechangerautobot"
        )

        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_voice_effects_keyboard(file_token, user_id, page=1)
        )

        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        asyncio.create_task(send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"🗣 <b>TTS OVOZ YARATILDI!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"📝 <b>Matn:</b> «<i>{data['text']}</i>»\n"
                f"🎙 <b>Ovoz:</b> {voice_info['name']}"
            )
        ))
    except Exception as e:
        logger.exception("Error in TTS: %s", e)
        await callback.message.reply(t(user_id, "error_processing"))


@dp.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    keyboard = get_voice_effects_keyboard(file_token, user_id, page=1)
    await callback.message.reply(t(user_id, "voice_ready"), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data.startswith("menu_amb:"))
async def handle_ambience_menu_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    keyboard = get_ambience_keyboard(file_token, user_id)
    await callback.message.reply(t(user_id, "ambience_ready"), reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()


@dp.callback_query(F.data.startswith("cancel:"))
async def handle_cancel_callback(callback: CallbackQuery):
    user_id = callback.from_user.id
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.pop(file_token, None)
    if data and "path" in data and data["path"].exists():
        data["path"].unlink(missing_ok=True)
    TEXT_STORAGE.pop(file_token, None)
    await callback.message.edit_text(t(user_id, "cancelled"))
    await callback.answer(t(user_id, "cancelled"))


@dp.callback_query(F.data == "noop")
async def handle_noop(callback: CallbackQuery):
    await callback.answer()


# ---------------------- INLINE MODE HANDLER ----------------------

@dp.inline_query()
async def handle_inline_query(inline_query: InlineQuery, bot: Bot):
    """Handles inline queries to send 100% PURE native Telegram Voice Notes in any chat!"""
    import urllib.parse
    query = inline_query.query.strip()
    results = []

    if not query:
        results.append(
            InlineQueryResultArticle(
                id="hint",
                title="🎙 Ovozli xabar yaratish uchun matn yozing",
                description="Masalan: @voicechangerautobot Salom do'stlar!",
                input_message_content=InputTextMessageContent(
                    message_text="🎙 <b>Voice Changer Bot</b> orqali ovozli xabar yaratish uchun matn yozing!\n\n<i>Misol: @voicechangerautobot Bugun darsga bormayman</i>",
                    parse_mode=ParseMode.HTML
                )
            )
        )
        await inline_query.answer(results, cache_time=1, is_personal=True)
        return

    render_domain = os.getenv("RENDER_EXTERNAL_URL", "https://voice-changer-bot-5pts.onrender.com").rstrip("/")

    for idx, (v_key, v_info) in enumerate(TTS_VOICES.items()):
        encoded_text = urllib.parse.quote(query[:200])
        voice_url = f"{render_domain}/api/tts_voice?text={encoded_text}&voice={v_key}"

        results.append(
            InlineQueryResultVoice(
                id=f"v_{v_key}_{abs(hash(query))%1000000}",
                voice_url=voice_url,
                title=f"{v_info['name']}"
                # No caption parameter so Telegram sends ONLY the pure voice bubble!
            )
        )

    await inline_query.answer(results, cache_time=10, is_personal=True)


# ---------------------- HEALTH & IN-MEMORY TTS STREAM SERVER ----------------------

async def generate_tts_in_memory(text: str, voice_key: str) -> Optional[bytes]:
    """Generates OGG Opus voice in memory in ~300ms."""
    voice_info = TTS_VOICES.get(voice_key, TTS_VOICES["uz_female"])
    try:
        communicate = edge_tts.Communicate(text, voice_info["voice"])
        mp3_data = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_data.extend(chunk["data"])

        if not mp3_data:
            return None

        process = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y",
            "-i", "pipe:0",
            "-c:a", "libopus",
            "-b:a", "48k",
            "-application", "voip",
            "-frame_duration", "20",
            "-f", "ogg",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate(input=bytes(mp3_data))
        if process.returncode == 0 and stdout:
            return stdout
        return None
    except Exception as e:
        logger.exception("Error in generate_tts_in_memory: %s", e)
        return None


async def run_health_server():
    """Runs HTTP server with high-speed in-memory audio streaming for Telegram Voice Notes."""
    import os
    from aiohttp import web

    port = int(os.getenv("PORT", 10000))

    async def handle_ping(request):
        return web.Response(text="🎙 Voice Changer & TTS AI Bot is running 24/7!")

    async def handle_tts_voice_stream(request):
        """Streams pure OGG Opus directly to Telegram to render as a circular voice note."""
        text = request.query.get("text", "").strip()
        voice_key = request.query.get("voice", "uz_male")
        if not text:
            return web.Response(status=400, text="Missing text")

        ogg_data = await generate_tts_in_memory(text, voice_key)
        if not ogg_data:
            return web.Response(status=500, text="TTS generation failed")

        return web.Response(
            body=ogg_data,
            content_type="audio/ogg; codecs=opus",
            headers={
                "Content-Disposition": 'inline; filename="voice.ogg"',
                "Content-Length": str(len(ogg_data)),
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=86400"
            }
        )

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    app.router.add_get("/api/tts_voice", handle_tts_voice_stream)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Web server and in-memory TTS streaming running on port %s", port)


# ---------------------- MAIN ENTRYPOINT ----------------------

async def main():
    try:
        me = await main_bot.get_me()
        print("\n" + "=" * 60)
        print(f"🤖 Asosiy Bot: @{me.username} ({me.first_name})")
        log_me = await log_bot.get_me()
        print(f"🕵️‍♂️ Yordamchi Log Bot: @{log_me.username} ({log_me.first_name})")
        print("🎙 Voice Changer & Deep Analytics Bot 24/7 online!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"❌ Ulanishda xatolik: {e}")
        return

    asyncio.create_task(cleanup_old_files())
    await run_health_server()

    await asyncio.gather(
        dp.start_polling(main_bot),
        log_dp.start_polling(log_bot)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
