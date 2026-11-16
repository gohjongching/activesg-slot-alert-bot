import sys
import time
import random
import logging
from datetime import datetime

from config import Config
from db import init_db, is_slot_recently_alerted, record_slot_alert, clean_old_slots
from notifier import test_telegram_connection, format_slot_alert, send_telegram_message
from scraper import ActiveSGScraper

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ActiveSGBot")

def run_check_cycle(scraper: ActiveSGScraper):
    logger.info(f"Starting check cycle for {Config.ACTIVITY.title()} across venues: {Config.MONITORED_VENUES or 'ALL'}")
    slots = scraper.check_slots()
    logger.info(f"Scraper returned {len(slots)} potential slots.")

    new_alerts_count = 0
    for slot in slots:
        venue = slot["venue"]
        activity = slot["activity"]
        date = slot["date"]
        time_slot = slot["time_slot"]
        court_no = slot.get("court_no")
        booking_url = slot.get("booking_url", Config.BASE_URL)

        # Unique identifier for this slot
        slot_id = f"{venue}_{activity}_{date}_{time_slot}_{court_no or ''}".lower().replace(" ", "_")

        if not is_slot_recently_alerted(slot_id, cooldown_hours=3):
            # Format and send alert
            alert_text = format_slot_alert(
                venue=venue,
                activity=activity,
                date=date,
                time_slot=time_slot,
                court_no=court_no,
                booking_url=booking_url
            )
            success = send_telegram_message(alert_text)
            if success:
                record_slot_alert(
                    slot_id=slot_id,
                    venue=venue,
                    activity=activity,
                    date=date,
                    time_slot=time_slot,
                    court_no=court_no
                )
                new_alerts_count += 1
                logger.info(f"Alert sent for slot: {venue} | {date} {time_slot}")
                # Brief sleep between messages to avoid Telegram rate limits
                time.sleep(1)

    logger.info(f"Cycle completed. Sent {new_alerts_count} new alerts.")

def main():
    logger.info("Initializing ActiveSG Slot Alert Bot...")

    # 1. Validate Config
    errors = Config.validate()
    if errors:
        for err in errors:
            logger.error(f"[CONFIG ERROR] {err}")
        print("\nPlease update your .env file with your Telegram Bot Token and Chat ID.")
        sys.exit(1)

    # 2. Initialize Database
    init_db()
    logger.info("Database initialized successfully.")

    # 3. Test Telegram Credentials
    logger.info("Verifying Telegram connection...")
    if not test_telegram_connection():
        logger.error("Could not send test message to Telegram. Please check BOT_TOKEN and CHAT_ID in .env.")
        sys.exit(1)
    logger.info("Telegram connection verified! Check your Telegram for the confirmation ping.")

    # 4. Initialize Scraper
    scraper = ActiveSGScraper(headless=Config.HEADLESS)

    # 5. Continuous Loop
    logger.info(f"Bot running. Monitoring every ~{Config.CHECK_INTERVAL_SECONDS}s. Press Ctrl+C to stop.")
    while True:
        try:
            run_check_cycle(scraper)
            clean_old_slots(days_old=7)
        except Exception as e:
            logger.error(f"Unexpected error in check loop: {e}", exc_info=True)

        # Add randomized jitter to avoid predictable bot patterns (e.g. interval +/- 15%)
        jitter = random.randint(-10, 15)
        sleep_duration = max(30, Config.CHECK_INTERVAL_SECONDS + jitter)
        logger.info(f"Sleeping for {sleep_duration} seconds until next cycle...")
        time.sleep(sleep_duration)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
        sys.exit(0)
