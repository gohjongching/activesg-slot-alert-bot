import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    
    ACTIVITY = os.getenv("ACTIVITY", "badminton").strip().lower()
    
    # Comma-separated venues to monitor
    _venues = os.getenv("MONITORED_VENUES", "")
    MONITORED_VENUES = [v.strip() for v in _venues.split(",") if v.strip()]
    
    # Target days
    _days = os.getenv("TARGET_DAYS", "")
    TARGET_DAYS = [d.strip().capitalize() for d in _days.split(",") if d.strip()]
    
    # Target hours
    _hours = os.getenv("TARGET_HOURS", "")
    TARGET_HOURS = [h.strip() for h in _hours.split(",") if h.strip()]
    
    CHECK_INTERVAL_SECONDS = int(os.getenv("CHECK_INTERVAL_SECONDS", "90"))
    HEADLESS = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")

    BASE_URL = "https://activesg.gov.sg/facility-bookings/activities"
    DB_PATH = BASE_DIR / "slots.db"

    @classmethod
    def validate(cls):
        errors = []
        if not cls.TELEGRAM_BOT_TOKEN or cls.TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
            errors.append("TELEGRAM_BOT_TOKEN is missing or not set in .env")
        if not cls.TELEGRAM_CHAT_ID or cls.TELEGRAM_CHAT_ID == "your_telegram_chat_id_here":
            errors.append("TELEGRAM_CHAT_ID is missing or not set in .env")
        return errors
