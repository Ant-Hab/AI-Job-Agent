import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_telegram_alert(message, files=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("Telegram credentials missing in .env file!")
        return

    # 1. Send the text alert
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

    # 2. Upload the .tex files as attachments
    if files:
        doc_url = f"https://api.telegram.org/bot{token}/sendDocument"
        for file_path in files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        requests.post(doc_url, data={"chat_id": chat_id}, files={"document": f})
                except Exception as e:
                    print(f"Failed to send file {file_path}: {e}")
