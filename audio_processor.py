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

# Pure ElevenLabs Neural AI Personas (100% Neural Speech-to-Speech)
VOICE_EFFECTS = {
    # 1. 👴 Wise Elderly Grandfather (Bill - Authentic old grandfather voice)
    "ai_old_man": {
        "uz": "👴 Qari Oqsoqol Bobo",
        "ru": "👴 Мудрый Дедушка",
        "en": "👴 Wise Grandfather",
        "elevenlabs_id": "pqHfZKP75CvOlQylNhV4",
        "mode": "old_man",
        "desc_uz": "100% haqiqiy, titroqli va samimiy keksa oqsoqol bobo ovozi",
        "desc_ru": "100% реалистичный голос мудрого дедушки",
        "desc_en": "Authentic wise elderly grandfather voice"
    },
    # 2. 🧔‍♂️ Deep Mature Male / Big Man (Brian - Deep resonant baritone)
    "ai_deep_man": {
        "uz": "🧔‍♂️ Yo'g'on Katta Odam",
        "ru": "🧔‍♂️ Глубокий Мужской Голос",
        "en": "🧔‍♂️ Deep Mature Man",
        "elevenlabs_id": "nPczCjzI2devNBz1zQrb",
        "mode": "deep_man",
        "desc_uz": "Juda yo'g'on, salobatli va nufuzli katta erkak ovozi",
        "desc_ru": "Густой, авторитетный и низкий баритон взрослого мужчины",
        "desc_en": "Deep, authoritative and heavy mature baritone"
    },
    # 3. 🧒 Cute Little Child / Kid (Jessica - 5-7 year old playful kid)
    "ai_child": {
        "uz": "🧒 Kichkintoy Bola",
        "ru": "🧒 Маленький Ребенок",
        "en": "🧒 Cute Little Child",
        "elevenlabs_id": "cgSgspJ2msm6clMCkdW9",
        "mode": "child",
        "desc_uz": "5-7 yoshli shirin va yoqimli bolakay ovozi",
        "desc_ru": "Милый и естественный голос маленького ребенка",
        "desc_en": "Sweet and playful little kid persona"
    },
    # 4. 👩‍🦰 Sweet Natural Girl / Young Female (Bella - Crystal clear female)
    "ai_female": {
        "uz": "👩‍🦰 Mayin Qiz Bola / Ayol",
        "ru": "👩‍🦰 Нежная Девушка / Женский",
        "en": "👩‍🦰 Sweet Girl / Female",
        "elevenlabs_id": "EXAVITQu4vr4xnSDxMaL",
        "mode": "female",
        "desc_uz": "100% tabiiy, mayin va yoqimli qiz bola / ayol ovozi",
        "desc_ru": "100% естественный и приятный женский голос",
        "desc_en": "Hyper-realistic sweet and natural female voice"
    },
    # 5. 🐿 Alvin Chipmunk (Hollywood Cinema Studio Quality)
    "ai_chipmunk": {
        "uz": "🐿 Chipmunk (Alvin Burunduk)",
        "ru": "🐿 Бурундук Элвин",
        "en": "🐿 Alvin Chipmunk",
        "filter": "asetrate=48000*1.65,aresample=48000,atempo=0.606,equalizer=f=3400:t=q:w=1.4:g=6.5,equalizer=f=1200:t=q:w=1.8:g=3.0,highpass=f=260,treble=g=4.5,compand=0.02|0.05:0.1|0.1:-60/-60|-25/-12|0/-1:5:0:0:0.02,volume=1.3",
        "desc_uz": "Kulgili, sho'x va haqiqiy filmlardagi Alvin burunduk ovozi",
        "desc_ru": "Знаменитый веселый и чистый голос бурундука Элвина из фильма",
        "desc_en": "Authentic movie-quality Alvin and the Chipmunks voice"
    },
    # 6. 🎬 Hollywood Cinema Narrator (George - Warm captivating movie trailer voice)
    "ai_cinema": {
        "uz": "🎬 Gollivud Diktor",
        "ru": "🎬 Голливудский Диктор",
        "en": "🎬 Cinema Narrator",
        "elevenlabs_id": "JBFqnCBsd6RMkjVDRZzb",
        "mode": "cinema",
        "desc_uz": "Gollivud filmlari va treylerlaridagi chuqur diktor ovozi",
        "desc_ru": "Глубокий дикторский голос трейлеров Голливуда",
        "desc_en": "Deep cinematic movie narrator persona"
    },
    # 7. 🦸‍♂️ Action Movie Hero (Callum - Fierce warrior / action star)
    "ai_hero": {
        "uz": "🦸‍♂️ Jangovar Qahramon",
        "ru": "🦸‍♂️ Герой Экшна",
        "en": "🦸‍♂️ Action Movie Hero",
        "elevenlabs_id": "N2lVS1w4EtoT3dr4eOWO",
        "mode": "hero",
        "desc_uz": "Ekshn filmlar va o'yinlardagi kuchli jangchi qahramon ovozi",
        "desc_ru": "Голос брутального героя экшн-фильмов и игр",
        "desc_en": "Intense action movie hero persona"
    },
    # 8. 🎙 Lively Radio Host / DJ (Will - Energetic broadcast voice)
    "ai_radio": {
        "uz": "🎙 Radio Boshlovchi (DJ)",
        "ru": "🎙 Радио Ведущий (DJ)",
        "en": "🎙 Radio DJ Host",
        "elevenlabs_id": "bIHbv24MWmeRgasZH58o",
        "mode": "radio",
        "desc_uz": "Tiniq va energiyaga boy radio boshlovchisi ovozi",
        "desc_ru": "Энергичный голос ведущего радиошоу",
        "desc_en": "Lively and energetic radio DJ host"
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


async def convert_speech_to_speech_elevenlabs(
    input_audio: Path,
    voice_id: str,
    output_path: Path,
    mode: Optional[str] = None
) -> bool:
    """
    Transforms any voice audio into realistic ElevenLabs AI personas with auto key-pool failover!
    """
    import aiohttp
    import json
    from config import ELEVENLABS_KEYS

    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"

    # Acoustic Formant Shifter: Prepares input audio for perfect gender/character synthesis
    temp_in = output_path.with_suffix(".in_sts.mp3")
    if mode == "female":
        af_prep = "asetrate=44100*1.30,aresample=44100,atempo=0.769,equalizer=f=3200:t=q:w=1.5:g=3.5,highpass=f=180"
    elif mode == "child":
        af_prep = "asetrate=44100*1.28,aresample=44100,atempo=0.781,equalizer=f=3000:t=q:w=1.5:g=3.5,highpass=f=160"
    elif mode == "chipmunk":
        af_prep = "asetrate=44100*1.42,aresample=44100,atempo=0.704,highpass=f=250"
    elif mode == "deep_man":
        af_prep = "equalizer=f=220:t=q:w=1.5:g=3.0,highpass=f=50"
    elif mode == "old_man":
        af_prep = "equalizer=f=300:t=q:w=1.5:g=2.5,highpass=f=60"
    else:
        af_prep = "highpass=f=50"

    cmd_prep = [
        "ffmpeg", "-y",
        "-i", str(input_audio),
        "-af", af_prep,
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        "-b:a", "128k",
        str(temp_in)
    ]

    if not _run_ffmpeg_sync(cmd_prep) or not temp_in.exists():
        return False

    async with aiohttp.ClientSession() as session:
        for key in ELEVENLABS_KEYS:
            try:
                headers = {"xi-api-key": key}
                with open(temp_in, "rb") as f_audio:
                    data = aiohttp.FormData()
                    data.add_field("audio", f_audio, filename="audio.mp3", content_type="audio/mpeg")
                    data.add_field("model_id", "eleven_multilingual_sts_v2")
                    data.add_field(
                        "voice_settings",
                        json.dumps({
                            "similarity_boost": 0.38,
                            "stability": 0.52,
                            "style": 0.0,
                            "use_speaker_boost": True
                        })
                    )

                    async with session.post(url, headers=headers, data=data, timeout=45) as resp:
                        if resp.status == 200:
                            res_bytes = await resp.read()
                            temp_out = output_path.with_suffix(".out_sts.mp3")
                            with open(temp_out, "wb") as f_out:
                                f_out.write(res_bytes)

                            # Final mastering: crystal clear treble presence and rich speech volume
                            cmd_conv = [
                                "ffmpeg", "-y",
                                "-i", str(temp_out),
                                "-af", "volume=1.25,highpass=f=50,equalizer=f=3400:t=q:w=1.2:g=2.5",
                                "-c:a", "libopus",
                                "-b:a", "64k",
                                "-application", "voip",
                                str(output_path)
                            ]

                            success = _run_ffmpeg_sync(cmd_conv)
                            temp_out.unlink(missing_ok=True)
                            temp_in.unlink(missing_ok=True)
                            if success:
                                return True
                        elif resp.status in (401, 429):
                            logger.warning("ElevenLabs key quota/auth failed, rotating to next key...")
                            continue
                        else:
                            logger.error("ElevenLabs STS status %s: %s", resp.status, await resp.text())
            except Exception as err:
                logger.warning("ElevenLabs STS exception: %s, rotating...", err)
                continue

    temp_in.unlink(missing_ok=True)
    return False


async def apply_voice_effect(input_path: Path, output_path: Path, effect_key: str) -> bool:
    """Applies the selected voice effect via ElevenLabs AI or Hollywood DSP filter."""
    effect = VOICE_EFFECTS.get(effect_key)
    if not effect:
        logger.error("Unknown effect: %s", effect_key)
        return False

    # 1. Hollywood Cinema DSP (like Alvin Chipmunk)
    if "filter" in effect:
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-af", effect["filter"],
            "-c:a", "libopus",
            "-b:a", "64k",
            "-application", "voip",
            str(output_path)
        ]
        return await asyncio.to_thread(_run_ffmpeg_sync, cmd)

    # 2. ElevenLabs Neural AI Speech-to-Speech
    voice_id = effect.get("elevenlabs_id", "pqHfZKP75CvOlQylNhV4")
    mode = effect.get("mode")
    return await convert_speech_to_speech_elevenlabs(
        input_path,
        voice_id,
        output_path,
        mode=mode
    )


async def apply_ambience_effect(input_path: Path, output_path: Path, ambience_key: str) -> bool:
    """Mixes synthesized ambient background sounds with voice audio ultrafast."""
    ambience = AMBIENCE_EFFECTS.get(ambience_key)
    if not ambience:
        return False

    bg_source = ambience["source"]
    bg_vol = ambience.get("bg_vol", 0.4)
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
        "-b:a", "48k",
        "-application", "voip",
        str(output_path)
    ]
    return await asyncio.to_thread(_run_ffmpeg_sync, cmd)


async def generate_tts(text: str, voice_key: str, output_path: Path, style: str = "natural") -> bool:
    """Generates natural, highly-expressive neural speech with broadcast studio acoustic warmth."""
    voice_info = TTS_VOICES.get(voice_key, TTS_VOICES["uz_female"])
    voice_name = voice_info["voice"]

    rate = "+1%"
    pitch = "+1Hz"

    if "excited" in style:
        rate = "+8%"
        pitch = "+4Hz"
    elif "calm" in style:
        rate = "-5%"
        pitch = "-2Hz"

    try:
        communicate = edge_tts.Communicate(text, voice_name, rate=rate, pitch=pitch)
        temp_mp3 = output_path.with_suffix(".temp.mp3")
        await communicate.save(str(temp_mp3))

        studio_filter = (
            "equalizer=f=220:t=q:w=1.5:g=2.5,"
            "equalizer=f=3600:t=q:w=1.2:g=3.0,"
            "highpass=f=80,"
            "compand=0.02|0.05:0.1|0.1:-60/-60|-25/-12|0/-1:5:0:0:0.02"
        )

        cmd = [
            "ffmpeg", "-y",
            "-i", str(temp_mp3),
            "-af", studio_filter,
            "-c:a", "libopus",
            "-b:a", "64k",
            "-application", "voip",
            str(output_path)
        ]
        success = await asyncio.to_thread(_run_ffmpeg_sync, cmd)
        temp_mp3.unlink(missing_ok=True)
        return success
    except Exception as e:
        logger.exception("Error in generate_tts: %s", e)
        return False
