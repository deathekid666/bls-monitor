import os
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
import json

URL = "https://blsspainmorocco.com/casablanca/french/"

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

STATUS_FILE = "status.json"
STATE_FILE = "state.txt"


# ------------------------
# TELEGRAM
# ------------------------
def send(msg):
    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": msg},
        timeout=15
    )


# ------------------------
# FETCH CLEAN PAGE
# ------------------------
def get_page():
    r = requests.get(URL, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    for t in soup(["script", "style", "noscript", "svg", "img", "footer", "header"]):
        t.decompose()

    text = " ".join(soup.get_text(" ", strip=True).lower().split())
    fp = hashlib.sha256(text.encode()).hexdigest()

    return text, fp


# ------------------------
# STATE DETECTOR
# ------------------------
def detect(text):
    open_words = [
        "book appointment",
        "select appointment",
        "available appointment",
        "vacant slot"
    ]

    closed_words = [
        "fully booked",
        "no appointment",
        "no slots",
        "currently unavailable"
    ]

    score = 0

    for w in open_words:
        if w in text:
            score += 10

    for w in closed_words:
        if w in text:
            score -= 12

    return "OPEN" if score >= 10 else "CLOSED"


# ------------------------
# WRITE DASHBOARD JSON
# ------------------------
def write_dashboard(state, fp):
    data = {
        "state": state,
        "time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "hash": fp,
        "url": URL
    }

    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)


# ------------------------
# MAIN
# ------------------------
def run():
    print("LIVE DASHBOARD MODE")

    text, fp = get_page()
    state = detect(text)

    last = None
    if os.path.exists(STATE_FILE):
        last = open(STATE_FILE).read().strip()

    # first run
    if not last:
        with open(STATE_FILE, "w") as f:
            f.write(state)

        write_dashboard(state, fp)
        print("baseline saved")
        return

    changed = state != last

    # update dashboard ALWAYS
    write_dashboard(state, fp)

    # alert only on OPEN transition
    if last != "OPEN" and state == "OPEN":
        send("🚨 LIVE ALERT: APPOINTMENT OPENED\n\n" + URL)
        print("ALERT SENT")

    # save state
    with open(STATE_FILE, "w") as f:
        f.write(state)


if __name__ == "__main__":
    run()