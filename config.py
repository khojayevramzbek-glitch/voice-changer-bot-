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

TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
