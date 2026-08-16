import asyncio
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional
import static_ffmpeg
import edge_tts

# Initialize static ffmpeg binaries
static_ffmpeg.add_paths()

logger = logging.getLogger(__name__)

# 20+ Rich Voice Effects
VOICE_EFFECTS = {
    # Animals & Characters
    "chipmunk": {
        "uz": "🐿 Chipmunk (Burunduk)", "ru": "🐿 Бурундук", "en": "🐿 Chipmunk",
        "filter": "asetrate=48000*1.55,aresample=48000,atempo=0.85",
        "desc_uz": "Kulgili va quvnoq sincap ovozi",
        "desc_ru": "Смешной и веселый голос бурундука",
        "desc_en": "Funny and cheerful high-pitch voice"
    },
    "alien": {
        "uz": "👽 Alien (O'zga sayyoralik)", "ru": "👽 Пришелец", "en": "👽 Alien",
        "filter": "tremolo=f=12.0:d=0.8,asetrate=48000*1.25,aresample=48000,chorus=0.7:0.9:55:0.4:0.25:2",
        "desc_uz": "Kosmik titroqli begona ovoz",
        "desc_ru": "Инопланетный космический голос с вибрацией",
        "desc_en": "Cosmic vibrating extraterrestrial voice"
    },
    "robot": {
        "uz": "🤖 Robot (Kiborg)", "ru": "🤖 Робот", "en": "🤖 Robot",
        "filter": "chorus=0.7:0.9:15:0.4:0.25:2,equalizer=f=1000:t=q:w=1:g=6,flanger=delay=4:depth=2:speed=8",
        "desc_uz": "Mexanik temir kiborg ovozi",
        "desc_ru": "Механический металлический голос",
        "desc_en": "Mechanical cyborg metallic voice"
    },
    "monster": {
        "uz": "👹 Monster (Qalin maxluq)", "ru": "👹 Монстр", "en": "👹 Monster",
        "filter": "asetrate=48000*0.68,aresample=48000,atempo=1.1,bass=g=7",
        "desc_uz": "Chuqur, qo'rqinchli qalin bas ovoz",
        "desc_ru": "Глубокий грозный бас монстра",
        "desc_en": "Deep, scary and thick monster voice"
    },
    "helium": {
        "uz": "🎈 Geliy gazi (Helium)", "ru": "🎈 Гелиевый газ", "en": "🎈 Helium Gas",
        "filter": "asetrate=48000*1.75,aresample=48000,atempo=0.75",
        "desc_uz": "Shardagi geliy gazini yutgandek ovoz",
        "desc_ru": "Голос будто вдохнули гелий из шарика",
        "desc_en": "High squeaky helium balloon voice"
    },
    "ghost": {
        "uz": "👻 Arvoh (Ghost)", "ru": "👻 Призрак", "en": "👻 Ghost",
        "filter": "asetrate=48000*0.82,aresample=48000,aecho=0.8:0.9:600|1200:0.5|0.3,chorus=0.7:0.9:45:0.4:0.25:2",
        "desc_uz": "Vahimali va qo'rqinchli sharpali ovoz",
        "desc_ru": "Жуткий потусторонний голос призрака",
        "desc_en": "Spooky haunted paranormal voice"
    },
    "underwater": {
        "uz": "🌊 Suv osti (Underwater)", "ru": "🌊 Под водой", "en": "🌊 Underwater",
        "filter": "lowpass=f=450,volume=2.2,tremolo=f=4:d=0.5",
        "desc_uz": "Suv tubida gapirilgandek bo'g'iq ovoz",
        "desc_ru": "Глухой звук как под водой",
        "desc_en": "Muffled underwater swimming sound"
    },
    "megaphone": {
        "uz": "📢 Megafon (Rupor)", "ru": "📢 Мегафон", "en": "📢 Megaphone",
        "filter": "highpass=f=800,lowpass=f=2500,volume=3,acrusher=bits=10:mix=0.4:mode=log",
        "desc_uz": "Ko'chadagi baland megafon ovozi",
        "desc_ru": "Громкий уличный рупор мегафона",
        "desc_en": "Loud street megaphone / bullhorn"
    },
    "baby": {
        "uz": "👶 Chaqaloq ovozi (Baby)", "ru": "👶 Малыш", "en": "👶 Baby Voice",
        "filter": "asetrate=48000*1.38,aresample=48000,atempo=0.9",
        "desc_uz": "Kichkintoy yosh bola ovozi",
        "desc_ru": "Милый голос маленького ребенка",
        "desc_en": "Cute little toddler voice"
    },
    "wizard": {
        "uz": "🧙‍♂️ Sehrgar bobo (Wizard)", "ru": "🧙‍♂️ Мудрец / Старик", "en": "🧙‍♂️ Old Wizard",
        "filter": "asetrate=48000*0.78,aresample=48000,atempo=0.9,aecho=0.7:0.7:200:0.3",
        "desc_uz": "Qadimgi sehrgar yoki oqsoqol ovozi",
        "desc_ru": "Голос древнего мудреца или старца",
        "desc_en": "Wise old mystic elder voice"
    },
    "bassboost": {
        "uz": "🔊 Bass Boost (Earrape)", "ru": "🔊 Bass Boost (Мега бас)", "en": "🔊 Bass Boost",
        "filter": "bass=g=18:f=110,volume=1.8",
        "desc_uz": "Kuchaytirilgan tebranishli qalin bas",
        "desc_ru": "Мощный вибрирующий бас для мемов",
        "desc_en": "Massive booming boosted bass"
    },
    "radio": {
        "uz": "📻 Ratsiya (Walkie-Talkie)", "ru": "📻 Рация", "en": "📻 Walkie-Talkie",
        "filter": "highpass=f=900,lowpass=f=3200,volume=2.5,acrusher=bits=8:mix=0.5:mode=log",
        "desc_uz": "Politsiya / maxsus xizmat ratsiyasi",
        "desc_ru": "Полицейская служебная рация",
        "desc_en": "Police tactical walkie-talkie"
    },
    "telephone": {
        "uz": "☎️ Eski telefon", "ru": "☎️ Старый телефон", "en": "☎️ Vintage Phone",
        "filter": "bandpass=f=1600:w=1000,volume=2.2",
        "desc_uz": "90-yillardagi diskli uy telefoni ovozi",
        "desc_ru": "Звук старого дискового телефона",
        "desc_en": "90s landline telephone effect"
    },
    "echo": {
        "uz": "🏔 Aks-sado (Echo / G'or)", "ru": "🏔 Эхо / Пещера", "en": "🏔 Echo / Cave",
        "filter": "aecho=0.8:0.88:400|800:0.5|0.3",
        "desc_uz": "Tog'lar yoki katta g'ordagi aks-sado",
        "desc_ru": "Эхо в горах или огромной пещере",
        "desc_en": "Deep mountain cave echo effect"
    },
    "fast": {
        "uz": "⚡ Tezlashtirilgan (1.5x)", "ru": "⚡ Ускорение (1.5x)", "en": "⚡ Fast (1.5x)",
        "filter": "atempo=1.5",
        "desc_uz": "Tezkor shiddatli nutq",
        "desc_ru": "Быстрая динамичная речь",
        "desc_en": "Quick accelerated speech"
    },
    "slow": {
        "uz": "🐢 Sekinlashtirilgan (0.7x)", "ru": "🐢 Замедление (0.7x)", "en": "🐢 Slow (0.7x)",
        "filter": "atempo=0.7",
        "desc_uz": "Og'ir va sekin nutq",
        "desc_ru": "Медленная размеренная речь",
        "desc_en": "Slow and relaxed speech"
    },
    "reverse": {
        "uz": "🔄 Orqaga (Reverse)", "ru": "🔄 Задом наперед", "en": "🔄 Reverse Audio",
        "filter": "areverse",
        "desc_uz": "Ovozni teskari tartibda o'qish",
        "desc_ru": "Воспроизведение голоса задом наперед",
        "desc_en": "Plays audio backwards in reverse"
    },
    "audio8d": {
        "uz": "🎧 8D Ovoz (Aylanma)", "ru": "🎧 8D Аудио", "en": "🎧 8D Audio",
        "filter": "apulsator=hz=0.2:amount=1",
        "desc_uz": "Quloqchinlarda aylanib eshitiluvchi ovoz",
        "desc_ru": "Голос вращается вокруг головы в наушниках",
        "desc_en": "Pans seamlessly in 360 degrees"
    }
}

# Atmospheric Background Sounds synthesized via rich FFmpeg audio filters
AMBIENCE_EFFECTS = {
    "rain": {
        "uz": "🌧 Yomg'ir & Momaqaldiroq", "ru": "🌧 Дождь и гроза", "en": "🌧 Rain & Thunder",
        "source": "anoisesrc=d=120:c=brown:r=48000:a=0.15,lowpass=f=2600,highpass=f=180,volume=2.0",
        "bg_vol": 0.45, "voice_vol": 1.2
    },
    "ocean": {
        "uz": "🌊 Dengiz to'lqinlari", "ru": "🌊 Шум океана", "en": "🌊 Ocean Waves",
        "source": "anoisesrc=d=120:c=pink:r=48000:a=0.18,tremolo=f=0.12:d=0.95,lowpass=f=1300,volume=2.2",
        "bg_vol": 0.5, "voice_vol": 1.2
    },
    "wind": {
        "uz": "💨 Bo'ron & Shamol", "ru": "💨 Ветер и буря", "en": "💨 Wind & Storm",
        "source": "anoisesrc=d=120:c=pink:r=48000:a=0.16,tremolo=f=0.35:d=0.8,bandpass=f=650:w=450,volume=2.0",
        "bg_vol": 0.4, "voice_vol": 1.2
    },
    "fireplace": {
        "uz": "🔥 Kamin / Gulxan", "ru": "🔥 Уютный камин", "en": "🔥 Fireplace",
        "source": "anoisesrc=d=120:c=brown:r=48000:a=0.12,highpass=f=1600,volume=2.8",
        "bg_vol": 0.45, "voice_vol": 1.2
    },
    "cinematic": {
        "uz": "🎬 Epik Kinematik Zal", "ru": "🎬 Кинематографичный зал", "en": "🎬 Cinematic Hall",
        "source": "anoisesrc=d=120:c=brown:r=48000:a=0.04,lowpass=f=500",
        "bg_vol": 0.2, "voice_vol": 1.2,
        "voice_extra_filter": "aecho=0.8:0.9:500|1000:0.4|0.25,bass=g=8:f=100"
    }
}

# Neural TTS Voice Configurations
TTS_VOICES = {
    "uz_male": {"name": "🇺🇿 O'zbekcha (Erkak - Sardor)", "voice": "uz-UZ-SardorNeural", "lang": "uz"},
    "uz_female": {"name": "🇺🇿 O'zbekcha (Ayol - Madina)", "voice": "uz-UZ-MadinaNeural", "lang": "uz"},
    "ru_male": {"name": "🇷🇺 Русский (Мужской - Дмитрий)", "voice": "ru-RU-DmitryNeural", "lang": "ru"},
    "ru_female": {"name": "🇷🇺 Русский (Женский - Светлана)", "voice": "ru-RU-SvetlanaNeural", "lang": "ru"},
    "en_male": {"name": "🇬🇧 English (Male - Christopher)", "voice": "en-US-ChristopherNeural", "lang": "en"},
    "en_female": {"name": "🇬🇧 English (Female - Ana)", "voice": "en-US-AnaNeural", "lang": "en"}
}


def _run_ffmpeg_sync(cmd: list) -> bool:
    """Runs an ffmpeg command synchronously."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode != 0:
            logger.error("FFmpeg error: %s", res.stderr)
            return False
        return True
    except Exception as e:
        logger.exception("Exception running ffmpeg: %s", e)
        return False


async def apply_voice_effect(input_path: Path, output_path: Path, effect_key: str) -> bool:
    """Applies the selected voice effect to the audio file asynchronously."""
    effect = VOICE_EFFECTS.get(effect_key)
    if not effect:
        logger.error("Unknown effect: %s", effect_key)
        return False

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", effect["filter"],
        "-c:a", "libopus",
        "-b:a", "64k",
        "-vn",
        str(output_path)
    ]
    return await asyncio.to_thread(_run_ffmpeg_sync, cmd)


async def apply_ambience_effect(input_path: Path, output_path: Path, ambience_key: str) -> bool:
    """Mixes synthesized ambient background sounds with voice audio."""
    ambience = AMBIENCE_EFFECTS.get(ambience_key)
    if not ambience:
        return False

    bg_source = ambience["source"]
    bg_vol = ambience.get("bg_vol", 0.3)
    voice_vol = ambience.get("voice_vol", 1.2)
    extra_filter = ambience.get("voice_extra_filter", "")

    voice_filter = f"volume={voice_vol}"
    if extra_filter:
        voice_filter = f"{voice_filter},{extra_filter}"

    filter_complex = f"[0:a]{voice_filter}[v];[1:a]volume={bg_vol}[bg];[v][bg]amix=inputs=2:duration=first[out]"

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-f", "lavfi", "-i", bg_source,
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-c:a", "libopus",
        "-b:a", "64k",
        str(output_path)
    ]
    return await asyncio.to_thread(_run_ffmpeg_sync, cmd)


async def generate_tts(text: str, voice_key: str, output_path: Path) -> bool:
    """Generates natural neural speech using edge-tts."""
    voice_info = TTS_VOICES.get(voice_key, TTS_VOICES["uz_female"])
    try:
        communicate = edge_tts.Communicate(text, voice_info["voice"])
        temp_mp3 = output_path.with_suffix(".temp.mp3")
        await communicate.save(str(temp_mp3))

        # Convert generated MP3 to native Telegram OGG Opus format
        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_mp3),
            "-c:a", "libopus",
            "-b:a", "64k",
            str(output_path)
        ]
        success = await asyncio.to_thread(_run_ffmpeg_sync, cmd)
        temp_mp3.unlink(missing_ok=True)
        return success
    except Exception as e:
        logger.exception("Error in generate_tts: %s", e)
        return False
