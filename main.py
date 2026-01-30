import requests
from bs4 import BeautifulSoup
import time
import json
import os
import smtplib
from email.mime.text import MIMEText

# =====================
# KONFIGURATION
# =====================

URL = "https://kerebyudlejning.dk"
CHECK_INTERVAL = 10  # sekunder

EMAIL = os.getenv("EMAIL_USER")
PASSWORD = os.getenv("EMAIL_PASS")

SEEN_FILE = "seen.json"

# =====================
# EMAIL
# =====================

def send_email(subject, body):

    if not EMAIL or not PASSWORD:
        print("❌ Mangler EMAIL_USER eller EMAIL_PASS")
        return

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.send_message(msg)

        print("📧 Mail sendt")

    except Exception as e:
        print("❌ Mail-fejl:", e)


# =====================
# SEEN STORAGE
# =====================

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


seen = load_seen()

# =====================
# SCRAPER
# =====================

def check_site():

    print("🔍 Tjekker siden...")

    try:
        r = requests.get(URL, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.find_all("a", href=True)

        found_new = False

        for card in cards:

            text = card.get_text().lower()

            # Spring reserverede over
            if "reserveret" in text:
                continue

            link = card["href"]

            if not link.startswith("/"):
                continue

            if "/bolig" not in link:
                continue

            full_url = "https://kerebyudlejning.dk" + link

            if full_url not in seen:

                seen.add(full_url)
                save_seen(seen)

                found_new = True

                print("🏠 NY LEJLIGHED:", full_url)

                send_email(
                    "Ny ledig lejlighed på Kereby!",
                    f"Der er fundet en ny lejlighed:\n\n{full_url}"
                )

        if not found_new:
            print("Ingen nye lejligheder")

    except Exception as e:
        print("❌ Fejl:", e)


# =====================
# MAIN LOOP
# =====================

print("🤖 Kereby-bot startet")
send_email("Test fra Kereby-bot", "Hvis du får denne mail, virker det 👍")

while True:
    check_site()
    time.sleep(CHECK_INTERVAL)
