from flask import Flask
import threading
import time
import hashlib
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# =========================
# CONFIG
# =========================

URL = "https://blsspainmorocco.com/casablanca/french/"

CHECK_INTERVAL = 30

TELEGRAM_TOKEN = "8368264794:AAEAOD8js8_mVUuV7XQsAhpr_BRUplzorCw"
CHAT_ID = "6508714545"

# =========================
# FLASK APP (required for Render)
# =========================

app = Flask(__name__)

@app.route("/")
def home():
    return "BLS Monitor Running"

# =========================
# TELEGRAM
# =========================

def send_message(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": msg
            },
            timeout=15
        )
    except Exception as e:
        print("Telegram message error:", e)

def send_photo(image_bytes):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
            files={
                "photo": ("screen.png", image_bytes)
            },
            data={
                "chat_id": CHAT_ID
            },
            timeout=30
        )
    except Exception as e:
        print("Telegram photo error:", e)

# =========================
# SELENIUM SETUP
# =========================

def create_driver():

    options = Options()

    # Required for Render/Linux
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Pretend real browser
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)

    return driver

driver = create_driver()

# =========================
# PAGE ANALYSIS
# =========================

def analyze_page(html):

    html = html.lower()

    score = 0
    signals = []

    # Positive indicators
    positive = [
        "book appointment",
        "schedule appointment",
        "visa appointment",
        "select center"
    ]

    # Negative indicators
    negative = [
        "fully booked",
        "no appointment",
        "currently unavailable",
        "no slots"
    ]

    for p in positive:
        if p in html:
            score += 2
            signals.append(f"+ {p}")

    for n in negative:
        if n in html:
            score -= 3
            signals.append(f"- {n}")

    return score, signals

# =========================
# CHECK WEBSITE
# =========================

def check_website():

    driver.get(URL)

    time.sleep(5)

    html = driver.page_source

    screenshot = driver.get_screenshot_as_png()

    hash_value = hashlib.md5(html.encode()).hexdigest()

    score, signals = analyze_page(html)

    return {
        "hash": hash_value,
        "score": score,
        "signals": signals,
        "screenshot": screenshot
    }

# =========================
# MONITOR LOOP
# =========================

def monitor():

    print("Monitor started")

    send_message("🚀 BLS Monitor Started")

    last_hash = None
    last_score = -999

    while True:

        try:

            result = check_website()

            current_hash = result["hash"]
            current_score = result["score"]

            # First run
            if last_hash is None:
                last_hash = current_hash
                last_score = current_score

            # Detect meaningful change
            elif current_hash != last_hash:

                if current_score > last_score + 2:

                    message = "🚨 POSSIBLE APPOINTMENT CHANGE DETECTED\n\n"

                    if result["signals"]:
                        message += "Signals:\n"
                        message += "\n".join(result["signals"])
                        message += "\n\n"

                    message += URL

                    send_message(message)

                    send_photo(result["screenshot"])

                    print("Alert sent")

                last_hash = current_hash
                last_score = current_score

        except Exception as e:
            print("Monitor error:", e)

        time.sleep(CHECK_INTERVAL)

# =========================
# START THREAD
# =========================

threading.Thread(target=monitor, daemon=True).start()

# =========================
# START SERVER
# =========================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)