import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "8719968713:AAH8OeK7Y8LBwKx7KNmBM4VznlwCuFn3TBE").strip()
LOG_BOT_TOKEN = os.getenv("LOG_BOT_TOKEN", "8935735357:AAFsSTeoirZ5YAAVyGatSCrOn_eT5um2pnE").strip()

ADMIN_ID_RAW = os.getenv("ADMIN_ID", "8594505572").strip()
ADMIN_ID = int(ADMIN_ID_RAW) if ADMIN_ID_RAW.isdigit() else 8594505572

# Auto-Rotating ElevenLabs Key Pool
ELEVENLABS_KEYS = [
    "sk_df4bbfc92f0ced55dfa85307d241acc828f948e7b8ccb9cc",
    "sk_4f1458bbf86ea74af10a071ab05cbe70570f1b847044cc2c",
    "sk_9c2e889327df9f886dac4e5ddd48e0bcb617b8624c850e0b",
    "sk_0de60a8b833b74e28fb2921141de1749ac996175b29a58e6",
    "sk_a5c3374cdd919f82ed39a215a700be801d57926cbe1e5c65",
    "sk_e644a1528e2665a55811a1e9b884138025333a8f72515c05",
    "sk_5595d13d26e0945bbbf4287387891111cb162f9078e3bdbd",
    "sk_a1af652b15a5946203360731645d13676adc69fc71b66c83",
    "sk_9731781e6adb5344281916a7622d4ca8f99b4fd85492e68e",
    "sk_d4783b4ec001966771f4bd03dfae9910ba4b86ef27804856"
]

TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
