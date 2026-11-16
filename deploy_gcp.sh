#!/bin/bash
set -e

# ==============================================================================
# ActiveSG Alert Bot - GCP Debian 13 (Trixie) 1-Click Deployment Script
# Region: asia-southeast1-c (Singapore)
# ==============================================================================

echo "====================================================="
echo "  Deploying ActiveSG Slot Alert Bot to Debian VM"
echo "====================================================="

# 1. Update OS packages & install system requirements
echo "[1/5] Updating apt packages and installing system libraries..."
sudo apt update -y
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    xvfb \
    git \
    curl \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2

# 2. Setup Virtual Environment
echo "[2/5] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Install Python Dependencies
echo "[3/5] Installing Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Playwright browser binaries with Linux dependencies
echo "[4/5] Installing Playwright Chromium browser and OS deps..."
playwright install --with-deps chromium

# 5. Check .env configuration
if [ ! -f ".env" ]; then
    echo "[!] No .env file found. Copying .env.example..."
    cp .env.example .env
    echo "[IMPORTANT] Please edit .env with your TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID: nano .env"
fi

echo "====================================================="
echo " Deployment completed successfully!"
echo " To run the bot manually in the background:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo " To install as a 24/7 systemd background service:"
echo "   sudo cp activesg-bot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable --now activesg-bot"
echo "   sudo systemctl status activesg-bot"
echo "====================================================="
