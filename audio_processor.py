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

# 25+ Studio-Calibrated Professional Voice Effects
VOICE_EFFECTS = {
    # 🌟 ElevenLabs Neural AI Personas (State-of-the-Art Neural Speech-to-Speech)
    "ai_roger": {
        "uz": "👴 AI Qari Bobo (ElevenLabs)", "ru": "👴 AI Мудрый Дедушка (ElevenLabs)", "en": "👴 AI Roger Grandfather (ElevenLabs)",
        "elevenlabs_id": "CwhRBWXzGAHq8TQ4Fs17",
        "gender": "male",
        "desc_uz": "ElevenLabs sun'iy intellekti orqali 100% haqiqiy qari oqsoqol ovozi",
        "desc_ru": "100% реалистичный голос мудрого дедушки от ElevenLabs AI",
        "desc_en": "Hyper-realistic authentic elderly grandfather voice powered by ElevenLabs"
    },
    "ai_bella": {
        "uz": "👩‍🦰 AI Qiz Bola / Ayol (ElevenLabs)", "ru": "👩‍🦰 AI Девушка / Женский (ElevenLabs)", "en": "👩‍🦰 AI Bella Female (ElevenLabs)",
        "elevenlabs_id": "EXAVITQu4vr4xnSDxMaL",
        "gender": "female",
        "desc_uz": "100% tabiiy, mayin va yoqimli qiz bola / ayol ovozi",
        "desc_ru": "100% естественный и приятный голос девушки / женщины",
        "desc_en": "Hyper-realistic sweet and natural young female voice"
    },
    "ai_boss": {
        "uz": "👑 AI Yo'g'on Erkak / Boss (Brian)", "ru": "👑 AI Босс / Глубокий Баритон", "en": "👑 AI Mafia Boss (Brian)",
        "elevenlabs_id": "nPczCjzI2devNBz1zQrb",
        "gender": "male",
        "desc_uz": "Juda yo'g'on, salobatli va nufuzli katta boss ovozi",
        "desc_ru": "Густой, авторитетный и низкий баритон босса",
        "desc_en": "Heavy authoritative and deep movie boss baritone"
    },
    "ai_chipmunk": {
        "uz": "🐿 AI Chipmunk Burunduk (AI)", "ru": "🐿 AI Бурундук Элвин (AI)", "en": "🐿 AI Chipmunk Alvin (AI)",
        "elevenlabs_id": "TX3LPaxmHKxFdv7VOQHJ",
        "mode": "chipmunk",
        "desc_uz": "Kulgili va sho'x Alvin burunduk ovozi (AI Sifatli)",
        "desc_ru": "Веселый и чистый голос бурундука Элвина через AI",
        "desc_en": "Crystal clear animated chipmunk voice powered by AI"
    },
    "ai_child": {
        "uz": "🧒 AI Kichkintoy Bola (Child AI)", "ru": "🧒 AI Ребенок / Малыш", "en": "🧒 AI Little Child (Kid AI)",
        "elevenlabs_id": "AZnzlk1XvdvUeBnXmlld",
        "mode": "child",
        "desc_uz": "Kichkina 5-6 yoshli yoqimli bola ovozi",
        "desc_ru": "Милый и естественный голос маленького ребенка",
        "desc_en": "Adorable cute little kid / child persona"
    },
    "ai_george": {
        "uz": "🎬 AI Gollivud Diktor (George)", "ru": "🎬 AI Голливудский Диктор", "en": "🎬 AI Cinema Narrator (George)",
        "elevenlabs_id": "JBFqnCBsd6RMkjVDRZzb",
        "gender": "male",
        "desc_uz": "Gollivud filmlari va treylerlaridagi chuqur diktor ovozi",
        "desc_ru": "Глубокий дикторский голос трейлеров Голливуда",
        "desc_en": "Deep cinematic movie narrator persona"
    },
    "ai_callum": {
        "uz": "🦸‍♂️ AI Ekshn Qahramon (Callum)", "ru": "🦸‍♂️ AI Герой Экшна", "en": "🦸‍♂️ AI Action Hero (Callum)",
        "elevenlabs_id": "N2lVS1w4EtoT3dr4eOWO",
        "gender": "male",
        "desc_uz": "Ekshn filmlar va o'yinlardagi kuchli jangchi qahramon ovozi",
        "desc_ru": "Голос брутального героя экшн-фильмов и игр",
        "desc_en": "Intense action movie hero persona"
    },
    "ai_radio": {
        "uz": "🎙 AI Radio Boshlovchi (Will)", "ru": "🎙 AI Радио Ведущий", "en": "🎙 AI Radio Host (Will)",
        "elevenlabs_id": "bIHbv24MWmeRgasZH58o",
        "gender": "male",
        "desc_uz": "Tiniq va energiyaga boy radio boshlovchisi ovozi",
        "desc_ru": "Энергичный голос ведущего радиошоу",
        "desc_en": "Lively and energetic radio DJ host"
    },
    "ai_monster": {
        "uz": "👹 AI Kinematik Maxluq (AI)", "ru": "👹 AI Кино-Монстр", "en": "👹 AI Cinematic Monster",
        "elevenlabs_id": "N2lVS1w4EtoT3dr4eOWO",
        "post_filter": "asetrate=48000*0.72,aresample=48000,atempo=1.2,bass=g=12:f=100,aecho=0.8:0.6:40|80:0.3|0.2",
        "desc_uz": "Qo'rqinchli chuqur bas maxluq ovozi (AI)",
        "desc_ru": "Грозный глубокий голос монстра с эффектом эхо",
        "desc_en": "Deep demonic creature with cinematic reverb"
    },
    "ai_robot": {
        "uz": "🤖 AI Kiborg Robot (AI)", "ru": "🤖 AI Киборг Робот", "en": "🤖 AI Cyborg Robot",
        "elevenlabs_id": "onwK4e9ZLuTAKqWW03F9",
        "post_filter": "tremolo=f=40:d=0.9,chorus=0.7:0.9:25:0.4:0.25:2,equalizer=f=1400:t=q:w=1.2:g=7",
        "desc_uz": "Kelajak kiborgi va Daft Punk robot ovozi",
        "desc_ru": "Голос киборга будущего с вокодером",
        "desc_en": "Futuristic cyborg vocoder sound"
    },
    # 👴 Elderly Grandfather (DSP): Natural aged vocal tremor, warm throat body and elderly cadence
    "old_man": {
        "uz": "👴 Qari Chol (DSP Classic)", "ru": "👴 Мудрый Старик (DSP)", "en": "👴 Wise Old Grandfather (DSP)",
        "filter": "asetrate=48000*0.86,aresample=48000,atempo=1.162,vibrato=f=5.0:d=0.34,tremolo=f=4.6:d=0.22,equalizer=f=360:t=q:w=1.5:g=6.5,equalizer=f=1700:t=q:w=2.0:g=4.5,lowpass=f=3800,highpass=f=90,compand=0.02|0.05:0.1|0.1:-60/-60|-25/-12|0/-1:5:0:0:0.02",
        "desc_uz": "Haqiqiy nordon va titroqli keksalar / qari oqsoqol bobo ovozi",
        "desc_ru": "Реалистичный хриплый и дрожащий голос пожилого дедушки",
        "desc_en": "Authentic realistic elderly grandfather voice with natural vocal tremor"
    },
    # 🧔‍♂️ Deep Mature Adult Male: Heavy chest resonance & deep masculine baritone
    "deep_man": {
        "uz": "🧔‍♂️ Yo'g'on Katta Odam (Deep Voice)", "ru": "🧔‍♂️ Глубокий Мужской Голос", "en": "🧔‍♂️ Deep Mature Man",
        "filter": "asetrate=48000*0.82,aresample=48000,atempo=1.22,bass=g=11:f=110,equalizer=f=260:t=q:w=1.4:g=7,equalizer=f=3000:t=q:w=1.2:g=2.5",
        "desc_uz": "Juda yo'g'on, salobatli va jiddiy katta erkak ovozi",
        "desc_ru": "Густой, низкий и брутальный взрослый мужской баритон",
        "desc_en": "Deep, authoritative and heavy mature masculine baritone"
    },
    # 🐿 Alvin & the Chipmunks: Crystal-clear squeaky high pitch with formant boost
    "chipmunk": {
        "uz": "🐿 Chipmunk (Alvin Burunduk)", "ru": "🐿 Бурундук (Элвин)", "en": "🐿 Alvin Chipmunk",
        "filter": "asetrate=48000*1.68,aresample=48000,atempo=0.6,equalizer=f=3200:t=q:w=1.5:g=7,highpass=f=250,treble=g=4",
        "desc_uz": "Kulgili va sho'x Alvin burunduk ovozi (Yuqori sifatli)",
        "desc_ru": "Знаменитый веселый голос бурунудука Элвина",
        "desc_en": "Famous Alvin and the Chipmunks studio sound"
    },
    # 👹 Hollywood Demon Monster: Deep sub-octave with demonic chest resonance
    "monster": {
        "uz": "👹 Monster (Vahimali Maxluq)", "ru": "👹 Демонический Монстр", "en": "👹 Menacing Monster",
        "filter": "asetrate=48000*0.62,aresample=48000,atempo=1.2,bass=g=14:f=90,equalizer=f=250:t=q:w=2:g=5,aecho=0.8:0.6:40|80:0.3|0.2",
        "desc_uz": "Kinematik qo'rqinchli chuqur bas maxluq ovozi",
        "desc_ru": "Грозный глубокий голос кинематографичного монстра",
        "desc_en": "Deep cinema monster / demon voice"
    },
    # 🤖 Cyborg Robot: Ring-modulated vocoder metallic effect
    "robot": {
        "uz": "🤖 Robot (Kiborg / Daft Punk)", "ru": "🤖 Робот (Киборг)", "en": "🤖 Cyborg Robot",
        "filter": "tremolo=f=45:d=0.95,chorus=0.7:0.9:25:0.4:0.25:2,equalizer=f=1200:t=q:w=1.2:g=8,flanger=delay=3:depth=2:speed=6",
        "desc_uz": "Daft Punk uslubidagi metallik temir robot ovozi",
        "desc_ru": "Металлический голос киборга в стиле Daft Punk",
        "desc_en": "Daft Punk style ring-modulated cyborg"
    },
    # 👽 Alien: Extraterrestrial cosmic phaser
    "alien": {
        "uz": "👽 Alien (O'zga sayyoralik)", "ru": "👽 Пришелец", "en": "👽 Alien Extraterrestrial",
        "filter": "tremolo=f=16.0:d=0.85,asetrate=48000*1.3,aresample=48000,chorus=0.8:0.9:45:0.4:0.25:2,flanger=delay=5:depth=4:speed=2",
        "desc_uz": "Kosmik tebranishli o'zga sayyoralik ovozi",
        "desc_ru": "Космический голос пришельца с вибрацией",
        "desc_en": "Cosmic vibrating UFO alien persona"
    },
    # 🎈 Helium: Squeaky party helium balloon
    "helium": {
        "uz": "🎈 Geliy gazi (Helium)", "ru": "🎈 Гелиевый газ", "en": "🎈 Helium Balloon",
        "filter": "asetrate=48000*1.95,aresample=48000,atempo=0.52,highpass=f=350,equalizer=f=4000:t=q:w=1.5:g=8",
        "desc_uz": "Geliy gazini yutgandek kulgili ingichka ovoz",
        "desc_ru": "Очень высокий и тонкий голос от шарика с гелием",
        "desc_en": "Ultra high-pitch squeaky helium balloon"
    },
    # 👻 Ghost: Spooky haunted ethereal voice
    "ghost": {
        "uz": "👻 Arvoh (Spooky Ghost)", "ru": "👻 Призрак / Привидение", "en": "👻 Haunted Ghost",
        "filter": "asetrate=48000*0.82,aresample=48000,aecho=0.8:0.9:350|700|1050:0.5|0.35|0.2,flanger=delay=10:depth=5:speed=0.5,chorus=0.7:0.9:55:0.4:0.25:2",
        "desc_uz": "Vahimali va qo'rqinchli sharpali arvoh ovozi",
        "desc_ru": "Жуткий потусторонний голос призрака",
        "desc_en": "Haunted paranormal ghost whisper"
    },
    # 📢 Megaphone: Street bullhorn analog overdrive
    "megaphone": {
        "uz": "📢 Megafon (Bozorchi Rupori)", "ru": "📢 Мегафон / Рупор", "en": "📢 Loud Megaphone",
        "filter": "highpass=f=650,lowpass=f=2800,equalizer=f=1800:t=q:w=2:g=10,volume=3.5,acrusher=bits=8:mode=log:mix=0.35",
        "desc_uz": "Ko'chadagi baqiradigan baland megafon ovozi",
        "desc_ru": "Громкий уличный рупор громкоговорителя",
        "desc_en": "Loud street bullhorn with realistic horn resonance"
    },
    # 🌊 Underwater: Submerged submarine acoustics
    "underwater": {
        "uz": "🌊 Suv osti (Underwater)", "ru": "🌊 Под водой", "en": "🌊 Submerged Underwater",
        "filter": "lowpass=f=380,equalizer=f=150:t=q:w=1:g=8,tremolo=f=3.5:d=0.6,volume=3.0",
        "desc_uz": "Suv tubida gapirgandek bo'g'iq va to'lqinli ovoz",
        "desc_ru": "Глухой звук будто человек говорит под водой",
        "desc_en": "Deep submerged underwater acoustic sound"
    },
    # 👶 Baby Voice: Cute little toddler
    "baby": {
        "uz": "👶 Chaqaloq ovozi (Baby Voice)", "ru": "👶 Малыш", "en": "👶 Cute Baby Voice",
        "filter": "asetrate=48000*1.42,aresample=48000,atempo=0.88,equalizer=f=3000:t=q:w=2:g=4,highpass=f=200",
        "desc_uz": "Kichkintoy yoqimli chaqaloq ovozi",
        "desc_ru": "Милый детский голос маленького ребенка",
        "desc_en": "Cute toddler high-pitch voice"
    },
    # 🧙‍♂️ Wizard: Gandalf / Dumbledore mystic elder
    "wizard": {
        "uz": "🧙‍♂️ Sehrgar bobo (Wise Wizard)", "ru": "🧙‍♂️ Мудрый Старец / Маг", "en": "🧙‍♂️ Old Wizard",
        "filter": "asetrate=48000*0.76,aresample=48000,atempo=0.92,bass=g=10:f=120,aecho=0.8:0.7:150|300:0.3|0.15",
        "desc_uz": "Qadimgi buyuk sehrgar yoki dono oqsoqol ovozi",
        "desc_ru": "Голос древнего мудреца или волшебника",
        "desc_en": "Wise mystic elder Gandalf / Dumbledore voice"
    },
    # 🔊 Bass Boost: Heavy booming bass
    "bassboost": {
        "uz": "🔊 Bass Boost (300% Bas)", "ru": "🔊 Bass Boost (Мега бас)", "en": "🔊 Bass Boost 300%",
        "filter": "bass=g=22:f=100,equalizer=f=80:t=q:w=1:g=12,volume=1.6",
        "desc_uz": "Dinamikni tebratuvchi kuchli bas ovoz",
        "desc_ru": "Мощнейший сотрясающий бас",
        "desc_en": "Massive ear-shaking boosted bass"
    },
    # 📻 Police Walkie-Talkie
    "radio": {
        "uz": "📻 Ratsiya (Police Radio)", "ru": "📻 Полицейская рация", "en": "📻 Police Walkie-Talkie",
        "filter": "highpass=f=900,lowpass=f=3000,equalizer=f=2200:t=q:w=2:g=8,volume=2.8,acrusher=bits=8:mix=0.4:mode=log",
        "desc_uz": "Maxsus xizmat politsiya ratsiyasi ovozi",
        "desc_ru": "Звук служебной рации спецслужб",
        "desc_en": "Tactical police walkie-talkie with analog bandpass"
    },
    # ☎️ Vintage 90s Telephone
    "telephone": {
        "uz": "☎️ Eski 90-yillar telefoni", "ru": "☎️ Старый телефон 90-х", "en": "☎️ Vintage Landline Phone",
        "filter": "bandpass=f=1500:w=900,volume=2.6,highpass=f=500,lowpass=f=2500",
        "desc_uz": "90-yillardagi diskli uy telefoni ovozi",
        "desc_ru": "Звук старого дискового домашнего телефона",
        "desc_en": "90s landline telephone speaker"
    },
    # 🏔 Mountain Cave Echo
    "echo": {
        "uz": "🏔 Aks-sado (Grand Echo)", "ru": "🏔 Эхо в горах / Пещера", "en": "🏔 Grand Canyon Echo",
        "filter": "aecho=0.85:0.88:350|700|1050:0.5|0.35|0.2,treble=g=2",
        "desc_uz": "Tog'lar yoki katta g'ordagi tiniq aks-sado",
        "desc_ru": "Красивое объемное эхо в горах или пещере",
        "desc_en": "Deep spatial cave / grand canyon echo"
    },
    # ⚡ Fast 1.5x
    "fast": {
        "uz": "⚡ Tezlashtirilgan (1.5x)", "ru": "⚡ Ускорение (1.5x)", "en": "⚡ Fast (1.5x)",
        "filter": "atempo=1.5",
        "desc_uz": "Tezkor shiddatli nutq",
        "desc_ru": "Быстрая динамичная речь",
        "desc_en": "Quick accelerated speech"
    },
    # 🐢 Slow 0.7x
    "slow": {
        "uz": "🐢 Sekinlashtirilgan (0.7x)", "ru": "🐢 Замедление (0.7x)", "en": "🐢 Slow (0.7x)",
        "filter": "atempo=0.7",
        "desc_uz": "Og'ir va sekin nutq",
        "desc_ru": "Медленная размеренная речь",
        "desc_en": "Slow and relaxed speech"
    },
    # 🔄 Reverse
    "reverse": {
        "uz": "🔄 Orqaga (Reverse)", "ru": "🔄 Задом наперед", "en": "🔄 Reverse Audio",
        "filter": "areverse",
        "desc_uz": "Ovozni teskari tartibda o'qish",
        "desc_ru": "Воспроизведение голоса задом наперед",
        "desc_en": "Plays audio backwards in reverse"
    },
    # 🎧 8D Audio 360 Spatial
    "audio8d": {
        "uz": "🎧 8D Ovoz (360 Aylanma)", "ru": "🎧 8D Аудио (360°)", "en": "🎧 8D Spatial Audio",
        "filter": "apulsator=hz=0.18:amount=1,aecho=0.8:0.7:100:0.2",
        "desc_uz": "Quloqchinlarda bosh atrofida 360° aylanuvchi ovoz",
        "desc_ru": "Голос плавно вращается вокруг головы в наушниках",
        "desc_en": "360-degree spatial panning around head"
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
    is_female: bool = False,
    mode: Optional[str] = None,
    post_filter: Optional[str] = None
) -> bool:
    """
    Transforms any voice audio into realistic ElevenLabs AI personas with auto key-pool failover!
    """
    import aiohttp
    import json
    from config import ELEVENLABS_KEYS

    url = f"https://api.elevenlabs.io/v1/speech-to-speech/{voice_id}"

    # Prepare standard MP3 input with acoustic formant shifts
    temp_in = output_path.with_suffix(".in_sts.mp3")
    if is_female:
        af_prep = "asetrate=44100*1.32,aresample=44100,atempo=0.757,equalizer=f=3200:t=q:w=1.5:g=4,highpass=f=200"
    elif mode == "chipmunk":
        af_prep = "asetrate=44100*1.45,aresample=44100,atempo=0.69,highpass=f=250"
    elif mode == "child":
        af_prep = "asetrate=44100*1.22,aresample=44100,atempo=0.82,equalizer=f=2800:t=q:w=1.5:g=3"
    else:
        af_prep = ""

    if af_prep:
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
    else:
        cmd_prep = [
            "ffmpeg", "-y",
            "-i", str(input_audio),
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
                            "similarity_boost": 0.35,
                            "stability": 0.50,
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

                            # Build final output conversion with optional post filter
                            cmd_conv = ["ffmpeg", "-y", "-i", str(temp_out)]
                            if post_filter:
                                cmd_conv.extend(["-af", post_filter])
                            elif mode == "chipmunk":
                                cmd_conv.extend(["-af", "asetrate=48000*1.18,aresample=48000,atempo=0.847"])

                            cmd_conv.extend([
                                "-c:a", "libopus",
                                "-b:a", "64k",
                                "-application", "voip",
                                str(output_path)
                            ])

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
    """Applies the selected voice effect (ElevenLabs AI or Studio DSP)."""
    effect = VOICE_EFFECTS.get(effect_key)
    if not effect:
        logger.error("Unknown effect: %s", effect_key)
        return False

    # 1. ElevenLabs Speech-to-Speech AI
    if "elevenlabs_id" in effect:
        is_female = effect.get("gender") == "female"
        mode = effect.get("mode")
        post_filter = effect.get("post_filter")
        success = await convert_speech_to_speech_elevenlabs(
            input_path,
            effect["elevenlabs_id"],
            output_path,
            is_female=is_female,
            mode=mode,
            post_filter=post_filter
        )
        if success and output_path.exists():
            return True
        logger.warning("ElevenLabs fallback to DSP...")
        effect_filter = effect.get("filter", "asetrate=48000*0.86,aresample=48000,atempo=1.162,vibrato=f=5.0:d=0.34,tremolo=f=4.6:d=0.22,equalizer=f=360:t=q:w=1.5:g=6.5")
    else:
        effect_filter = effect.get("filter", "")

    # 2. Studio DSP Filter
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", effect_filter,
        "-c:a", "libopus",
        "-b:a", "48k",
        "-application", "voip",
        "-frame_duration", "20",
        "-vn",
        str(output_path)
    ]
    return await asyncio.to_thread(_run_ffmpeg_sync, cmd)


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
