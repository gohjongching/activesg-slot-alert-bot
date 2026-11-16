import logging
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from playwright.sync_api import sync_playwright, BrowserContext, Page, TimeoutError as PlaywrightTimeoutError
from config import Config

logger = logging.getLogger(__name__)

COOKIES_FILE = Path(__file__).resolve().parent / "session_cookies.json"

class ActiveSGScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = Config.BASE_URL

    def _setup_context(self, browser) -> BrowserContext:
        """
        Configures browser context with realistic Singapore user attributes
        to minimize Cloudflare bot flagging.
        """
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-SG",
            timezone_id="Asia/Singapore",
            geolocation={"longitude": 103.8198, "latitude": 1.3521},
            permissions=["geolocation"],
            java_script_enabled=True,
        )

        # Remove navigator.webdriver detection flag
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)

        # Load saved session cookies if available
        if COOKIES_FILE.exists():
            try:
                with open(COOKIES_FILE, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logger.info("Loaded existing session cookies.")
            except Exception as e:
                logger.warning(f"Could not load cookies from {COOKIES_FILE}: {e}")

        return context

    def _wait_for_cloudflare(self, page: Page, timeout_seconds: int = 20) -> bool:
        """
        Waits for Cloudflare challenge / Turnstile to complete.
        """
        logger.info("Checking for Cloudflare challenge...")
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            title = page.title().lower()
            if "just a moment" in title or "attention required" in title:
                logger.info("Cloudflare challenge page detected. Waiting for verification...")
                time.sleep(2)
            else:
                logger.info("Page loaded past Cloudflare.")
                return True
        logger.warning("Cloudflare challenge took too long or was not solved automatically.")
        return False

    def check_slots(self) -> List[Dict[str, Any]]:
        """
        Navigates ActiveSG facility schedule and extracts open slots
        matching monitored venues and target times.
        """
        open_slots: List[Dict[str, Any]] = []

        with sync_playwright() as p:
            # Launch Chromium with anti-bot evasion arguments
            browser = p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-infobars",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ]
            )

            context = self._setup_context(browser)
            page = context.new_page()

            try:
                logger.info(f"Navigating to {self.base_url}...")
                page.goto(self.base_url, wait_until="domcontentloaded", timeout=45000)
                
                # Handle Cloudflare check
                self._wait_for_cloudflare(page, timeout_seconds=15)
                
                # Wait for main content or booking activity elements
                page.wait_for_load_state("networkidle", timeout=15000)

                # Save current cookies for subsequent quick runs
                cookies = context.cookies()
                with open(COOKIES_FILE, "w", encoding="utf-8") as f:
                    json.dump(cookies, f, indent=2)

                # Parse facility listings and available slots
                open_slots = self._extract_slots_from_page(page)

            except PlaywrightTimeoutError:
                logger.error("Navigation timed out. Capturing debug screenshot...")
                page.screenshot(path="debug_timeout.png")
            except Exception as e:
                logger.error(f"Error during slot checking: {e}", exc_info=True)
                try:
                    page.screenshot(path="debug_error.png")
                    with open("debug_page.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                except Exception:
                    pass
            finally:
                browser.close()

        return open_slots

    def _extract_slots_from_page(self, page: Page) -> List[Dict[str, Any]]:
        """
        Parses DOM elements for available booking cards / slots.
        """
        slots = []
        
        # Example selector parsing:
        # In MyActiveSG+, cards or calendar blocks denote facility name, available status, and time.
        # We query all facility cards or slot items.
        content = page.content()
        logger.info(f"Page title: {page.title()} | HTML size: {len(content)} bytes")

        # Select all facility / slot container elements
        # (This adapts to both direct activity cards and slot lists)
        cards = page.locator("[data-testid*='facility'], .facility-card, [class*='FacilityCard'], [class*='SlotCard'], div[role='article']").all()
        
        logger.info(f"Found {len(cards)} facility/slot elements on page.")

        for card in cards:
            text = card.inner_text().strip()
            if not text:
                continue

            # Check if this card matches any of our monitored venues
            matched_venue = None
            for v in Config.MONITORED_VENUES:
                if v.lower() in text.lower():
                    matched_venue = v
                    break

            if Config.MONITORED_VENUES and not matched_venue:
                continue

            # Check if there are available slots mentioned
            if "available" in text.lower() or "book" in text.lower() or "slots" in text.lower():
                slot_info = {
                    "venue": matched_venue or "ActiveSG Venue",
                    "activity": Config.ACTIVITY,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "time_slot": "Available Slot (Check Portal)",
                    "court_no": None,
                    "booking_url": page.url,
                    "raw_text": text[:150]
                }
                slots.append(slot_info)

        return slots
