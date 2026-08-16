import asyncio
import logging
import sys
import uuid
import shutil
from pathlib import Path
from typing import Dict

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
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, TEMP_DIR
from audio_processor import apply_voice_effect, VOICE_EFFECTS
from keyboards import get_voice_effects_keyboard, get_after_effect_keyboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("VoiceChangerBot")

# In-memory mapping of file_token -> stored file information
# Structure: { file_token: { "path": Path, "user_id": int, "created_at": float } }
AUDIO_STORAGE: Dict[str, dict] = {}


async def cleanup_old_files():
    """Periodically cleans up files older than 30 minutes."""
    while True:
        try:
            await asyncio.sleep(600)  # Check every 10 minutes
            import time
            now = time.time()
            expired_tokens = []
            for token, data in list(AUDIO_STORAGE.items()):
                if now - data.get("created_at", now) > 1800:
                    expired_tokens.append(token)
                    try:
                        if data["path"].exists():
                            data["path"].unlink(missing_ok=True)
                    except Exception as e:
                        logger.error("Error deleting file %s: %s", data["path"], e)
            for token in expired_tokens:
                AUDIO_STORAGE.pop(token, None)
        except Exception as e:
            logger.error("Error in cleanup task: %s", e)


dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Handles /start command with an introduction and guide."""
    user_name = message.from_user.first_name if message.from_user else "Do'stim"
    text = (
        f"👋 <b>Assalomu alaykum, {user_name}!</b>\n\n"
        "🎙 <b>Voice Changer Bot</b>ga xush kelibsiz!\n\n"
        "Men siz yuborgan har qanday <b>ovozli xabar (voice)</b> yoki audio faylni turli xil qiziqarli ovozlarga o'zgartirib beraman!\n\n"
        "🔥 <b>Mavjud ovoz effektlari:</b>\n"
        "• 🐿 <b>Chipmunk</b> — Kulgili sincap ovozi\n"
        "• 👽 <b>Alien</b> — O'zga sayyoralik\n"
        "• 🤖 <b>Robot</b> — Mexanik kiborg ovozi\n"
        "• 👹 <b>Monster</b> — Chuqur qalin maxluq ovozi\n"
        "• 🎈 <b>Geliy gazi</b> — O'ta ingichka geliy ovozi\n"
        "• 🏔 <b>Aks-sado (Echo)</b> — G'or effekti\n"
        "• 📻 <b>Ratsiya</b> — Politsiya/harbiy ratsiyasi\n"
        "• ☎️ <b>Eski telefon</b> — 90-yillar qo'ng'irog'i\n"
        "• ⚡ <b>Tezlashtirish</b> / 🐢 <b>Sekinlashtirish</b>\n"
        "• 🔄 <b>Orqaga (Reverse)</b> & 🎧 <b>8D Ovoz</b>\n\n"
        "🚀 <b>Boshlash uchun:</b> Menga shunchaki <b>ovozli xabar (voice)</b> yoki audio yuboring!"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(Command("help"))
@dp.message(Command("effects"))
async def cmd_help(message: Message):
    """Lists and explains all voice effects."""
    effects_list = "\n".join(
        [f"• <b>{eff['name']}</b>: <i>{eff['description']}</i>" for eff in VOICE_EFFECTS.values()]
    )
    text = (
        "🎭 <b>Barcha mavjud ovoz effektlari:</b>\n\n"
        f"{effects_list}\n\n"
        "🎙 <i>Sinab ko'rish uchun hoziroq ovozli xabar yuboring!</i>"
    )
    await message.answer(text, parse_mode=ParseMode.HTML)


@dp.message(F.voice | F.audio | F.video_note)
async def handle_incoming_voice(message: Message, bot: Bot):
    """Downloads incoming voice/audio and presents effect options."""
    import time
    user_id = message.from_user.id if message.from_user else 0
    file_token = uuid.uuid4().hex[:10]

    status_msg = await message.reply("📥 <i>Ovozli xabar qabul qilindi, yuklab olinmoqda...</i>", parse_mode=ParseMode.HTML)

    try:
        # Determine file object
        if message.voice:
            file_id = message.voice.file_id
            ext = ".ogg"
            source_type = "🎙 Ovozli xabar"
        elif message.audio:
            file_id = message.audio.file_id
            ext = ".mp3"
            source_type = "🎵 Audio fayl"
        else:
            file_id = message.video_note.file_id
            ext = ".mp4"
            source_type = "📹 Video xabar"

        file = await bot.get_file(file_id)
        if not file.file_path:
            await status_msg.edit_text("❌ Fayl yuklab olishda xatolik yuz berdi.")
            return

        dest_path = TEMP_DIR / f"{file_token}_input{ext}"
        await bot.download_file(file.file_path, destination=dest_path)

        # Store file in memory
        AUDIO_STORAGE[file_token] = {
            "path": dest_path,
            "user_id": user_id,
            "created_at": time.time(),
            "source_type": source_type
        }

        keyboard = get_voice_effects_keyboard(file_token)
        await status_msg.edit_text(
            f"✨ <b>{source_type} tayyor!</b>\n\n"
            "Qaysi ovoz effektiga o'zgartirmoqchisiz? Quyidagi tugmalardan birini tanlang:",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.exception("Error downloading voice: %s", e)
        await status_msg.edit_text("❌ Ovozni yuklab olishda xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.")


@dp.callback_query(F.data.startswith("fx:"))
async def handle_effect_callback(callback: CallbackQuery, bot: Bot):
    """Applies the selected effect and sends the voice note back."""
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Noto'g'ri so'rov.", show_alert=True)
        return

    _, effect_key, file_token = parts
    effect = VOICE_EFFECTS.get(effect_key)

    if not effect:
        await callback.answer("Effekt topilmadi.", show_alert=True)
        return

    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer("⚠️ Bu ovozli xabar muddati tugagan. Iltimos, yangi ovoz yuboring.", show_alert=True)
        return

    await callback.answer(f"⏳ {effect['name']} qo'llanmoqda...")
    processing_msg = await callback.message.reply(
        f"⚙️ <b>{effect['name']}</b> effekti qo'llanmoqda... Iltimos kuting...",
        parse_mode=ParseMode.HTML
    )

    output_path = TEMP_DIR / f"{file_token}_{effect_key}.ogg"

    try:
        success = await apply_voice_effect(data["path"], output_path, effect_key)
        if not success or not output_path.exists():
            await processing_msg.edit_text("❌ Ovozni o'zgartirishda xatolik yuz berdi.")
            return

        bot_info = await bot.get_me()
        bot_username = bot_info.username or "VoiceChangerBot"

        voice_file = FSInputFile(output_path)
        caption = (
            f"✨ <b>Effekt:</b> {effect['name']}\n"
            f"📝 <i>{effect['description']}</i>\n\n"
            f"🤖 @{bot_username}"
        )

        await callback.message.reply_voice(
            voice=voice_file,
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=get_after_effect_keyboard(file_token)
        )
        await processing_msg.delete()

    except Exception as e:
        logger.exception("Error processing voice effect: %s", e)
        await processing_msg.edit_text("❌ Effektni qo'llashda xatolik yuz berdi.")
    finally:
        # Clean up processed output file after sending
        if output_path.exists():
            try:
                output_path.unlink(missing_ok=True)
            except Exception:
                pass


@dp.callback_query(F.data.startswith("menu:"))
async def handle_menu_callback(callback: CallbackQuery):
    """Reopens the voice effects selection menu for the same audio."""
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.get(file_token)
    if not data or not data["path"].exists():
        await callback.answer("⚠️ Ovoz muddati tugagan. Yangi ovoz yuboring.", show_alert=True)
        return

    keyboard = get_voice_effects_keyboard(file_token)
    await callback.message.reply(
        "🎭 <b>Boshqa effekt tanlang:</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@dp.callback_query(F.data == "info:effects")
async def handle_info_callback(callback: CallbackQuery):
    """Shows modal popup with information about all effects."""
    effects_summary = "\n".join([f"• {e['name']}: {e['description']}" for e in VOICE_EFFECTS.values()])
    await callback.message.answer(
        f"ℹ️ <b>Barcha ovoz effektlari haqida:</b>\n\n{effects_summary}",
        parse_mode=ParseMode.HTML
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("cancel:"))
async def handle_cancel_callback(callback: CallbackQuery):
    """Cancels and cleans up the stored file."""
    file_token = callback.data.split(":")[1]
    data = AUDIO_STORAGE.pop(file_token, None)
    if data and data["path"].exists():
        try:
            data["path"].unlink(missing_ok=True)
        except Exception:
            pass
    await callback.message.edit_text("❌ Bekor qilindi.")
    await callback.answer("Bekor qilindi.")


async def run_health_server():
    """Runs a minimal HTTP server for cloud platforms (Render, Koyeb, Railway)."""
    import os
    from aiohttp import web

    port = int(os.getenv("PORT", 0))
    if not port:
        return

    async def handle_ping(request):
        return web.Response(text="🎙 Voice Changer Bot is running 24/7!")

    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health check web server running on port %s", port)


async def main():
    """Main application runner."""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("\n" + "=" * 60)
        print("❌ XATOLIK: Telegram Bot Token kiritilmagan!")
        print("Iltimos, .env faylini oching va BOT_TOKEN qatoriga Telegram bot tokeningizni yozing.")
        print("Misol:")
        print("BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        print("=" * 60 + "\n")
        return

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Test bot token connectivity
    try:
        me = await bot.get_me()
        print("\n" + "=" * 60)
        print(f"🤖 Bot muvaffaqiyatli ishga tushdi: @{me.username} ({me.first_name})")
        print("🎙 Voice Changer Bot ovozli xabarlarni kutmoqda...")
        print("=" * 60 + "\n")
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ Telegram Botga ulanishda xatolik: {e}")
        print("Iltimos, bot tokeningiz to'g'riligini tekshiring.")
        print("=" * 60 + "\n")
        return

    # Start background cleanup task
    asyncio.create_task(cleanup_old_files())

    # Start health check server if running on cloud
    await run_health_server()

    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 Bot to'xtatildi.")
