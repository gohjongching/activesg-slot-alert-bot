import logging
import httpx
from typing import Optional
from config import Config

logger = logging.getLogger(__name__)

SPORT_EMOJIS = {
    "badminton": "🏸",
    "tennis": "🎾",
    "table tennis": "🏓",
    "squash": "🎯",
    "gym": "🏋️",
    "swimming": "🏊",
    "basketball": "🏀",
    "volleyball": "🏐"
}

def format_slot_alert(
    venue: str,
    activity: str,
    date: str,
    time_slot: str,
    court_no: Optional[str] = None,
    booking_url: Optional[str] = None
) -> str:
    emoji = SPORT_EMOJIS.get(activity.lower(), "📍")
    url = booking_url or Config.BASE_URL
    court_text = f"\n🏟️ <b>Court / Hall:</b> {court_no}" if court_no else ""
    
    message = (
        f"{emoji} <b>ActiveSG Slot Available!</b>\n\n"
        f"🏅 <b>Activity:</b> {activity.title()}\n"
        f"🏢 <b>Venue:</b> {venue}\n"
        f"📅 <b>Date:</b> {date}\n"
        f"⏰ <b>Time:</b> {time_slot}"
        f"{court_text}\n\n"
        f"👉 <a href=\"{url}\">Book on ActiveSG Now</a>"
    )
    return message

def send_telegram_message(text: str) -> bool:
    """
    Sends an HTML-formatted message to the configured Telegram Chat ID.
    """
    if not Config.TELEGRAM_BOT_TOKEN or not Config.TELEGRAM_CHAT_ID:
        logger.error("Telegram credentials missing in Config.")
        return False

    api_url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": Config.TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(api_url, json=payload)
            if resp.status_code == 200:
                logger.info("Telegram notification sent successfully.")
                return True
            else:
                logger.error(f"Failed to send Telegram message: {resp.status_code} - {resp.text}")
                return False
    except Exception as e:
        logger.error(f"Telegram API request failed: {e}")
        return False

def test_telegram_connection() -> bool:
    """
    Sends a test ping to verify bot credentials.
    """
    test_message = (
        "🤖 <b>ActiveSG Slot Alert Bot Connected!</b>\n\n"
        "Your Telegram bot credentials are valid and ready to receive alerts."
    )
    return send_telegram_message(test_message)
