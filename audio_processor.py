import asyncio
import subprocess
import logging
from pathlib import Path
import static_ffmpeg

# Initialize static ffmpeg binaries
static_ffmpeg.add_paths()

logger = logging.getLogger(__name__)

# List of available effects with Uzbek names, emojis, and ffmpeg audio filter chains
VOICE_EFFECTS = {
    "chipmunk": {
        "name": "🐿 Chipmunk (Burunduk)",
        "filter": "asetrate=48000*1.55,aresample=48000,atempo=0.85",
        "description": "O'ta ingichka va kulgili sincap ovozi"
    },
    "alien": {
        "name": "👽 Alien (O'zga sayyoralik)",
        "filter": "tremolo=f=12.0:d=0.8,asetrate=48000*1.25,aresample=48000,chorus=0.7:0.9:55:0.4:0.25:2",
        "description": "Kosmik titroqli begona ovoz"
    },
    "robot": {
        "name": "🤖 Robot (Kiborg)",
        "filter": "chorus=0.7:0.9:15:0.4:0.25:2,equalizer=f=1000:t=q:w=1:g=6,flanger=delay=4:depth=2:speed=8",
        "description": "Mexanik metall ovoz"
    },
    "monster": {
        "name": "👹 Monster (Maxluq / Qalin)",
        "filter": "asetrate=48000*0.68,aresample=48000,atempo=1.1,bass=g=7",
        "description": "Chuqur, qo'rqinchli qalin bas ovoz"
    },
    "helium": {
        "name": "🎈 Geliy gazi (Helium)",
        "filter": "asetrate=48000*1.75,aresample=48000,atempo=0.75",
        "description": "Shardagi geliy gazini yutgandek ingichka ovoz"
    },
    "echo": {
        "name": "🏔 Aks-sado (Echo / G'or)",
        "filter": "aecho=0.8:0.88:400|800:0.5|0.3",
        "description": "G'or yoki katta gumbazdagi aks-sado"
    },
    "radio": {
        "name": "📻 Ratsiya (Walkie-Talkie)",
        "filter": "highpass=f=900,lowpass=f=3200,volume=2.5,acrusher=bits=8:mix=0.5:mode=log",
        "description": "Harbiy yoki politsiya ratsiyasi effekti"
    },
    "telephone": {
        "name": "☎️ Eski telefon",
        "filter": "bandpass=f=1600:w=1000,volume=2.2",
        "description": "Eski 90-yillar uy telefoni ovozi"
    },
    "fast": {
        "name": "⚡ Tezlashtirilgan (1.5x)",
        "filter": "atempo=1.5",
        "description": "Tezkor nutq effekti"
    },
    "slow": {
        "name": "🐢 Sekinlashtirilgan (0.7x)",
        "filter": "atempo=0.7",
        "description": "Og'ir va sekinlashtirilgan nutq"
    },
    "reverse": {
        "name": "🔄 Orqaga (Reverse)",
        "filter": "areverse",
        "description": "Ovozni teskari o'qish effekti"
    },
    "audio8d": {
        "name": "🎧 8D Ovoz (Aylanma)",
        "filter": "apulsator=hz=0.2:amount=1",
        "description": "Quloqchinlarda aylanib eshitiluvchi ovoz"
    }
}


def _run_ffmpeg_sync(input_path: Path, output_path: Path, filter_str: str) -> bool:
    """Synchronous FFmpeg execution with proper flags."""
    cmd = [
        "ffmpeg",
        "-y",                   # Overwrite output
        "-i", str(input_path),  # Input audio file
        "-af", filter_str,      # Audio filter chain
        "-c:a", "libopus",      # Telegram native voice format codec
        "-b:a", "64k",          # Clean bitrate for voice
        "-vn",                  # Disable video if present
        str(output_path)
    ]
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

    return await asyncio.to_thread(_run_ffmpeg_sync, input_path, output_path, effect["filter"])
