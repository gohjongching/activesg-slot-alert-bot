import sys
from config import Config
from notifier import test_telegram_connection

def main():
    print("=" * 50)
    print("Testing Telegram Connection...")
    print("=" * 50)

    errors = Config.validate()
    if errors:
        print("\n❌ Configuration errors detected in .env:")
        for e in errors:
            print(f" - {e}")
        print("\nPlease copy .env.example to .env and fill in your actual credentials.")
        sys.exit(1)

    print(f"Bot Token : {Config.TELEGRAM_BOT_TOKEN[:10]}... (masked)")
    print(f"Chat ID   : {Config.TELEGRAM_CHAT_ID}")
    print("\nSending test message...")

    success = test_telegram_connection()
    if success:
        print("\n✅ SUCCESS: Test message sent! Please check your Telegram chat.")
    else:
        print("\n❌ FAILED: Could not send message to Telegram. Check your token/chat ID and internet connection.")

if __name__ == "__main__":
    main()
