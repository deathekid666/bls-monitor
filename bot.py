import os
import requests
from bs4 import BeautifulSoup

URL = "https://blsspainmorocco.com/casablanca/french/"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

POSITIVE_KEYWORDS = [
    "appointment",
    "book",
    "schedule",
    "available",
    "select",
    "slot"
]

NEGATIVE_KEYWORDS = [
    "fully booked",
    "no appointment",
    "currently unavailable",
    "no slots"
]

def send_message(msg):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )

def check_site():
    r = requests.get(URL, timeout=20)
    text = r.text.lower()

    score = 0
    signals = []

    for w in POSITIVE_KEYWORDS:
        if w in text:
            score += 2
            signals.append(f"+ {w}")

    for w in NEGATIVE_KEYWORDS:
        if w in text:
            score -= 3
            signals.append(f"- {w}")

    return score, signals

def run():
    print("Checking...")

    score, signals = check_site()

    if score > 2:
        msg = "🚨 POSSIBLE APPOINTMENT UPDATE\n\n"
        msg += "\n".join(signals)
        msg += "\n\n" + URL

        send_message(msg)
        print("ALERT SENT")
    else:
        print("No alert")

if __name__ == "__main__":
    run()