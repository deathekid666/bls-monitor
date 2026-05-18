import os
import time
import requests
import hashlib

URL = "https://blsspainmorocco.com/casablanca/french/"
CHECK_INTERVAL = 60

TELEGRAM_TOKEN = os.getenv("8368264794:AAEAOD8js8_mVUuV7XQsAhpr_BRUplzorCw")
CHAT_ID = os.getenv("6508714545")

def send(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_hash():
    headers = {"User-Agent": "Mozilla/5.0"}

    r = requests.get(URL, headers=headers, timeout=10)
    r.raise_for_status()

    text = " ".join(r.text.lower().split())

    keywords = [
        "appointment",
        "available",
        "slot",
        "fully booked",
        "no appointments",
        "currently unavailable"
    ]

    filtered = " ".join([w for w in text.split() if any(k in w for k in keywords)])

    if not filtered:
        filtered = text[:2000]

    return hashlib.md5(filtered.encode()).hexdigest()

def run():
    print("Bot started")
    send("Bot started")

    last = None

    while True:
        try:
            current = get_hash()

            if last is None:
                last = current

            elif current != last:
                send("🚨 Change detected!\n" + URL)
                last = current

        except Exception as e:
            print(e)

        time.sleep(CHECK_INTERVAL)

run()