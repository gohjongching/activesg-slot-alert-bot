# ActiveSG Slot Alert Bot (Telegram)

An automated slot monitoring and alert bot designed for Singapore's **ActiveSG / MyActiveSG+** facility booking system. It tracks open and cancelled slots (e.g. Badminton, Tennis, Squash, Gym) across your chosen sports halls and pushes real-time notifications to your Telegram chat with direct 1-click booking links.

---

## 📁 Project Structure

```
tele alert bot/
├── .env.example          # Configuration template
├── config.py             # Loads and validates environment variables
├── db.py                 # SQLite database for caching & deduplication (prevents alert spam)
├── notifier.py           # Formats messages and sends them via Telegram Bot API
├── scraper.py            # Playwright stealth scraper for ActiveSG portal
├── main.py               # Main monitoring loop with randomized jitter & auto-cleanup
├── test_notifier.py      # Quick script to verify your Telegram Bot Token & Chat ID
├── deploy_gcp.sh         # 1-click setup script for GCP VM (Debian 13 Trixie)
├── activesg-bot.service  # Systemd service file for 24/7 background running on GCP
└── requirements.txt      # Python dependencies
```

---

## 🚀 Step 1: Get Your Telegram Credentials

1. **Create Bot & Get Token:**
   * Open Telegram and search for [@BotFather](https://t.me/BotFather).
   * Send `/newbot`, name your bot, and copy the **API Token** (e.g. `7123456789:AAH...`).
2. **Get Your Telegram Chat ID:**
   * Search for [@userinfobot](https://t.me/userinfobot) on Telegram and hit `/start`.
   * Copy your numeric **Id** (e.g. `123456789`).
3. **Start a Chat with Your Bot:**
   * Open your newly created bot in Telegram and click **Start** (or send `/start`). This allows the bot to message you.

---

## ⚙️ Step 2: Configure `.env`

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Sport to monitor: badminton, tennis, squash, gym, table tennis
ACTIVITY=badminton

# Monitored Venues (comma-separated, case-insensitive)
MONITORED_VENUES=Clementi,Jurong East,Bishan,Delta,Heartbeat@Bedok

# Days of the week to monitor (leave empty for all)
TARGET_DAYS=Fri,Sat,Sun

# Target hours to monitor (leave empty for all)
TARGET_HOURS=18:00,19:00,20:00,21:00

# Polling frequency in seconds (default: 90)
CHECK_INTERVAL_SECONDS=90

HEADLESS=true
```

---

## 🧪 Step 3: Test Locally

1. Test your Telegram credentials:
   ```bash
   python test_notifier.py
   ```
   If successful, you will receive a test ping on your phone immediately!

2. Run the bot:
   ```bash
   python main.py
   ```

---

## ☁️ Step 4: Deploy to Your GCP VM (Debian 13 in `asia-southeast1-c`)

Because your VM is in Singapore, latency is minimal and uptime is 24/7.

1. **SSH into your GCP VM:**
   ```bash
   gcloud compute ssh <YOUR_VM_NAME> --zone=asia-southeast1-c
   ```

2. **Copy or Git Clone your project files onto the VM:**
   ```bash
   # Inside your VM directory (e.g. ~/tele-alert-bot)
   git clone <your-repo> tele-alert-bot
   cd tele-alert-bot
   ```

3. **Run the 1-click installer:**
   ```bash
   chmod +x deploy_gcp.sh
   ./deploy_gcp.sh
   ```

4. **Fill in your `.env` on the VM:**
   ```bash
   nano .env
   ```

5. **Start as a 24/7 Background System Service:**
   ```bash
   # Adjust path in activesg-bot.service if your directory is not /root/tele-alert-bot
   sudo cp activesg-bot.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now activesg-bot
   ```

6. **Check live logs on GCP:**
   ```bash
   sudo journalctl -u activesg-bot -f
   ```

---

## 🛡️ Anti-Spam & Anti-Ban Features
* **SQLite Deduplication (`db.py`):** Automatically remembers slots that were already notified. It will not spam your phone for the same open slot.
* **Random Jitter:** Check intervals vary automatically (e.g., 90s ± 15s) so access patterns look human and avoid tripping WAF rate limits.
* **Session Persistence:** Saves session cookies locally to minimize repetitive Cloudflare Turnstile challenges.
