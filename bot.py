import asyncio
import logging
import sys
import uuid
import time
from datetime import datetime
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
    InputTextMessageContent
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
    get_statistics, get_recent_users, get_all_user_ids,
    set_admin_id, get_admin_id
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("VoiceChangerBot")

# In-memory storage for pending audio and text sessions
AUDIO_STORAGE: Dict[str, dict] = {}
TEXT_STORAGE: Dict[str, dict] = {}

# Bot instances
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


# ==================== LOG BOT HANDLERS ====================

@log_dp.message(CommandStart())
async def log_cmd_start(message: Message):
    """When owner starts the Helper Bot, securely links their chat ID."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Xo'jayin"

    set_admin_id(user_id)
    text = (
        f"👑 <b>Assalomu alaykum, {name}!</b>\n\n"
        "🕵️‍♂️ <b>Men sizning rasmiy Yordamchi / Log Botingizman!</b>\n\n"
        "Asosiy Voice Botga kelgan <b>barcha ma'lumotlar</b> to'g'ridan-to'g'ri shu yerga keladi:\n"
        "• 👤 Yangi kirgan odamlar (Ismi, Username, ID)\n"
        "• 🎙 Ular yuborgan <b>ASL ovozli xabarlar</b> (audio)\n"
        "• ✨ Ular o'zgartirgan <b>tayyor ovozlar</b>\n"
        "• ✍️ Ular yozgan matnlar\n\n"
        f"✅ <b>Sizning Admin ID raqamingiz muvaffaqiyatli ulandi:</b> <code>{user_id}</code>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@log_dp.message(Command("stats"))
async def log_cmd_stats(message: Message):
    """Stats check from log bot."""
    stats = get_statistics()
    recent = get_recent_users(8)

    recent_text = ""
    for idx, u in enumerate(recent, 1):
        dt = datetime.fromtimestamp(u["last_active"]).strftime("%H:%M %d/%m")
        u_name = u["first_name"] or "Noma'lum"
        u_tag = f"(@{u['username']})" if u["username"] else ""
        recent_text += f"{idx}. <b>{u_name}</b> {u_tag} — <i>{dt}</i> (🎙{u['voice_count']})\n"

    text = (
        "📊 <b>BOTNING STATISTIKASI</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎙 <b>O'zgartirilgan ovozlar:</b> {stats['total_voices']} ta\n"
        f"✍️ <b>Matndan ovozlar (TTS):</b> {stats['total_tts']} ta\n\n"
        "🕒 <b>Oxirgi faol foydalanuvchilar:</b>\n"
        f"{recent_text if recent_text else 'Hozircha foydalanuvchilar yoq.'}"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


# ==================== MAIN VOICE BOT HANDLERS ====================

@dp.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    """Start command handler."""
    user_id = message.from_user.id if message.from_user else 0
    name = message.from_user.first_name if message.from_user else "Do'stim"
    username = message.from_user.username if message.from_user else None

    # Automatically set @khojayev_ramz as permanent admin
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
                f"🕒 <b>Vaqt:</b> {datetime.now().strftime('%H:%M:%S (%d/%m/%Y)')}"
            )
        )

    # Default language
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


@dp.message(Command("admin"))
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Shows stats to admin on main bot."""
    user_id = message.from_user.id if message.from_user else 0
    admin_id = get_current_admin_id()

    if admin_id and user_id != admin_id:
        await message.reply("⛔ Bu buyruq faqat bot administratori uchun.")
        return

    stats = get_statistics()
    recent = get_recent_users(8)

    recent_text = ""
    for idx, u in enumerate(recent, 1):
        dt = datetime.fromtimestamp(u["last_active"]).strftime("%H:%M %d/%m")
        u_name = u["first_name"] or "Noma'lum"
        u_tag = f"(@{u['username']})" if u["username"] else ""
        recent_text += f"{idx}. <b>{u_name}</b> {u_tag} — <i>{dt}</i> (🎙{u['voice_count']})\n"

    text = (
        "📊 <b>BOTNING STATISTIKASI VA ADMIN PANELI</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🎙 <b>O'zgartirilgan ovozlar:</b> {stats['total_voices']} ta\n"
        f"✍️ <b>Matndan qilingan ovozlar (TTS):</b> {stats['total_tts']} ta\n\n"
        "🕒 <b>Oxirgi faol foydalanuvchilar:</b>\n"
        f"{recent_text if recent_text else 'Hozircha foydalanuvchilar yoq.'}\n"
        "📢 <i>Barcha foydalanuvchilarga xabar tarqatish: /send [xabar matni]</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("send"))
@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot):
    """Broadcasts a message to all bot users."""
    user_id = message.from_user.id if message.from_user else 0
    admin_id = get_current_admin_id()

    if admin_id and user_id != admin_id:
        await message.reply("⛔ Bu buyruq faqat bot administratori uchun.")
        return

    text_to_send = message.text.replace("/send", "", 1).replace("/broadcast", "", 1).strip()
    if not text_to_send:
        await message.reply("⚠️ Xabar matnini kiriting!\nMisol: <code>/send Yangi ovoz effektlari qo'shildi!</code>", parse_mode=ParseMode.HTML)
        return

    user_ids = get_all_user_ids()
    sent_count = 0

    status_msg = await message.reply(f"📤 {len(user_ids)} ta foydalanuvchiga xabar yuborilmoqda...")

    for u_id in user_ids:
        try:
            await bot.send_message(chat_id=u_id, text=f"📢 <b>Bot Yangiligi:</b>\n\n{text_to_send}", parse_mode=ParseMode.HTML)
            sent_count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass

    await status_msg.edit_text(f"✅ Xabar <b>{sent_count} / {len(user_ids)}</b> ta foydalanuvchiga yetkazildi!", parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
@dp.message(F.text.in_(["ℹ️ Yordam", "ℹ️ Помощь", "ℹ️ Help"]))
async def cmd_help(message: Message):
    """Help command handler."""
    user_id = message.from_user.id if message.from_user else 0
    title = t(user_id, "help_title")
    text = t(user_id, "help_text")
    await message.answer(f"{title}\n\n{text}", parse_mode=ParseMode.HTML)


@dp.message(Command("lang"))
@dp.message(F.text.in_(["🌐 Tilni O'zgartirish", "🌐 Сменить язык", "🌐 Change Language"]))
async def cmd_language(message: Message):
    """Language switcher menu."""
    user_id = message.from_user.id if message.from_user else 0
    await message.answer(
        t(user_id, "lang_choose"),
        reply_markup=get_language_keyboard(),
        parse_mode=ParseMode.HTML
    )


@dp.message(F.text.in_(["✍️ Matndan Ovozga (TTS)", "✍️ Озвучка текста (TTS)", "✍️ Text-to-Speech"]))
async def cmd_tts_info(message: Message):
    """Prompt user to send text for Text-to-Speech."""
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
    """Info for background ambience sounds."""
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
    """Downloads incoming voice/audio and presents effect options."""
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

        # Send original voice audio to Helper Log Bot!
        u_tag = f"@{username}" if username else "yo'q"
        await send_to_log_bot(
            voice_path=dest_path,
            caption=(
                f"📥 <b>YANGI ASL OVOZ KELDI!</b>\n\n"
                f"👤 <b>Kimdan:</b> {name} ({u_tag})\n"
                f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
                f"📂 <b>Turi:</b> {media_type}\n"
                f"🕒 <b>Vaqt:</b> {datetime.now().strftime('%H:%M:%S')}"
            )
        )

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
    """Handles text input to convert into speech."""
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

    # Log text to Helper Bot
    u_tag = f"@{username}" if username else "yo'q"
    await send_to_log_bot(
        text=(
            f"✍️ <b>MATN YOZILDI (TTS):</b>\n\n"
            f"👤 <b>Kimdan:</b> {name} ({u_tag})\n"
            f"📝 <b>Matn:</b> «<i>{text_content}</i>»"
        )
    )

    keyboard = get_tts_keyboard(text_token, user_id)
    await message.reply(
        f"✍️ <i>«{text_content[:60]}...»</i>\n\n{t(user_id, 'text_received')}",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


# ---------------------- CALLBACK QUERY HANDLERS ----------------------

@dp.callback_query(F.data.startswith("setlang:"))
async def handle_set_language(callback: CallbackQuery):
    """Changes user's interface language."""
    user_id = callback.from_user.id
    lang_code = callback.data.split(":")[1]
    set_user_lang(user_id, lang_code)

    await callback.message.edit_text(
        t(user_id, "lang_changed"),
        parse_mode=ParseMode.HTML
    )
    await callback.message.answer(
        t(user_id, "start_desc"),
        reply_markup=get_main_menu_keyboard(user_id),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("page:"))
async def handle_pagination(callback: CallbackQuery):
    """Handles effect menu pagination."""
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
    """Applies voice filter and returns transformed voice message."""
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
    proc_msg = await callback.message.reply(
        t(user_id, "processing_effect", name=effect_name),
        parse_mode=ParseMode.HTML
    )

    output_path = TEMP_DIR / f"{file_token}_{effect_key}.ogg"

    try:
        success = await apply_voice_effect(data["path"], output_path, effect_key)
        if not success or not output_path.exists():
            await proc_msg.edit_text(t(user_id, "error_processing"))
            return

        increment_voice(user_id)

        # Send transformed voice to Helper Log Bot!
        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        await send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"✨ <b>O'ZGARTIRILGAN OVOZ!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"🎭 <b>Tanlangan Effekt:</b> {effect_name}"
            )
        )

        bot_info = await bot.get_me()
        bot_username = bot_info.username or "voicechangerautobot"

        caption = f"✨ <b>Effekt:</b> {effect_name}\n📝 <i>{desc}</i>\n\n🤖 @{bot_username}"

        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_after_effect_keyboard(file_token, user_id)
        )
        await proc_msg.delete()
    except Exception as e:
        logger.exception("Error in voice effect: %s", e)
        await proc_msg.edit_text(t(user_id, "error_processing"))
    finally:
        output_path.unlink(missing_ok=True)


@dp.callback_query(F.data.startswith("amb:"))
async def handle_ambience_callback(callback: CallbackQuery, bot: Bot):
    """Mixes ambient sound with voice."""
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

    proc_msg = await callback.message.reply(
        f"🌧 <b>{amb_name}</b> fon tovushi qo'shilmoqda...",
        parse_mode=ParseMode.HTML
    )

    output_path = TEMP_DIR / f"{file_token}_{amb_key}.ogg"
    try:
        success = await apply_ambience_effect(data["path"], output_path, amb_key)
        if not success or not output_path.exists():
            await proc_msg.edit_text(t(user_id, "error_processing"))
            return

        increment_voice(user_id)

        # Log Ambience to Helper bot
        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        await send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"🌧 <b>FON QO'SHILGAN OVOZ!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"🌧 <b>Tanlangan Fon:</b> {amb_name}"
            )
        )

        bot_info = await bot.get_me()
        bot_username = bot_info.username or "voicechangerautobot"

        caption = f"🌧 <b>Fon:</b> {amb_name}\n\n🤖 @{bot_username}"
        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_after_effect_keyboard(file_token, user_id)
        )
        await proc_msg.delete()
    except Exception as e:
        logger.exception("Error in ambience effect: %s", e)
        await proc_msg.edit_text(t(user_id, "error_processing"))
    finally:
        output_path.unlink(missing_ok=True)


@dp.callback_query(F.data.startswith("tts:"))
async def handle_tts_callback(callback: CallbackQuery, bot: Bot):
    """Generates natural speech from text, then offers voice effects."""
    user_id = callback.from_user.id
    parts = callback.data.split(":")
    voice_key, text_token = parts[1], parts[2]

    data = TEXT_STORAGE.get(text_token)
    if not data:
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    voice_info = TTS_VOICES.get(voice_key, TTS_VOICES["uz_female"])
    await callback.answer("🎙 Nutq tayyorlanmoqda...")

    proc_msg = await callback.message.reply(
        t(user_id, "processing_tts", name=voice_info["name"]),
        parse_mode=ParseMode.HTML
    )

    file_token = uuid.uuid4().hex[:10]
    output_path = TEMP_DIR / f"{file_token}_tts.ogg"

    try:
        success = await generate_tts(data["text"], voice_key, output_path)
        if not success or not output_path.exists():
            await proc_msg.edit_text(t(user_id, "error_processing"))
            return

        increment_tts(user_id)

        AUDIO_STORAGE[file_token] = {
            "path": output_path,
            "user_id": user_id,
            "created_at": time.time(),
            "first_name": data.get("first_name", "Foydalanuvchi"),
            "username": data.get("username")
        }

        # Log TTS voice to Helper Bot
        u_name = data.get("first_name", "Foydalanuvchi")
        u_tag = f"@{data.get('username')}" if data.get('username') else "yo'q"
        await send_to_log_bot(
            voice_path=output_path,
            caption=(
                f"🗣 <b>TTS OVOZ YARATILDI!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {u_name} ({u_tag})\n"
                f"📝 <b>Matn:</b> «<i>{data['text']}</i>»\n"
                f"🎙 <b>Ovoz:</b> {voice_info['name']}"
            )
        )

        bot_info = await bot.get_me()
        bot_username = bot_info.username or "voicechangerautobot"

        caption = (
            f"✍️ <i>«{data['text'][:80]}»</i>\n\n"
            f"🗣 <b>Ovoz:</b> {voice_info['name']}\n"
            f"🤖 @{bot_username}"
        )

        await callback.message.reply_voice(
            voice=FSInputFile(output_path),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_voice_effects_keyboard(file_token, user_id, page=1)
        )
        await proc_msg.delete()
    except Exception as e:
        logger.exception("Error in TTS: %s", e)
        await proc_msg.edit_text(t(user_id, "error_processing"))


@dp.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery):
    """Reopens effect menu."""
    user_id = callback.from_user.id
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    keyboard = get_voice_effects_keyboard(file_token, user_id, page=1)
    await callback.message.reply(
        t(user_id, "voice_ready"),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("menu_amb:"))
async def handle_ambience_menu_callback(callback: CallbackQuery):
    """Opens ambience background sounds menu."""
    user_id = callback.from_user.id
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer(t(user_id, "expired"), show_alert=True)
        return

    keyboard = get_ambience_keyboard(file_token, user_id)
    await callback.message.reply(
        t(user_id, "ambience_ready"),
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cancel:"))
async def handle_cancel_callback(callback: CallbackQuery):
    """Cancels and deletes temporary session."""
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
    """Handles inline queries to send voice messages in any chat directly."""
    query = inline_query.query.strip()
    results = []

    if not query:
        results.append(
            InlineQueryResultArticle(
                id="hint",
                title="🎙 Ovozli xabar yaratish uchun matn yozing",
                description="Masalan: @voicechangerautobot Salom do'stlar!",
                input_message_content=InputTextMessageContent(
                    message_text="🎙 <b>Voice Changer Bot</b> orqali ovozli xabar yaratish uchun matn yozing!",
                    parse_mode=ParseMode.HTML
                )
            )
        )
        await inline_query.answer(results, cache_time=5, is_personal=True)
        return

    bot_info = await bot.get_me()
    bot_username = bot_info.username or "voicechangerautobot"

    for idx, (v_key, v_info) in enumerate(TTS_VOICES.items()):
        results.append(
            InlineQueryResultArticle(
                id=f"inline_{v_key}_{idx}",
                title=f"🗣 {v_info['name']}",
                description=f"«{query[:50]}» matnini ovozda yuborish",
                input_message_content=InputTextMessageContent(
                    message_text=f"🎙 <b>{v_info['name']}:</b>\n«{query}»\n\n🤖 @{bot_username}",
                    parse_mode=ParseMode.HTML
                )
            )
        )

    await inline_query.answer(results, cache_time=10, is_personal=True)


# ---------------------- HEALTH CHECK SERVER ----------------------

async def run_health_server():
    """Runs a minimal HTTP server for cloud platforms (Render, Koyeb, Railway)."""
    import os
    from aiohttp import web

    port = int(os.getenv("PORT", 0))
    if not port:
        return

    async def handle_ping(request):
        return web.Response(text="🎙 Voice Changer & TTS AI Bot is running 24/7!")

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health check web server running on port %s", port)


# ---------------------- MAIN ENTRYPOINT ----------------------

async def main():
    try:
        me = await main_bot.get_me()
        print("\n" + "=" * 60)
        print(f"🤖 Asosiy Bot: @{me.username} ({me.first_name})")
        log_me = await log_bot.get_me()
        print(f"🕵️‍♂️ Yordamchi Log Bot: @{log_me.username} ({log_me.first_name})")
        print("🎙 Voice Changer & Dual Log Bot 24/7 online!")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"❌ Ulanishda xatolik: {e}")
        return

    asyncio.create_task(cleanup_old_files())
    await run_health_server()

    # Run polling for both main bot and log bot simultaneously!
    await asyncio.gather(
        dp.start_polling(main_bot),
        log_dp.start_polling(log_bot)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
