import requests
from bs4 import BeautifulSoup
import time
import json
import os

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# =====================
# KONFIG
# =====================

URL = "https://kerebyudlejning.dk"
CHECK_INTERVAL = 30  # sekunder (tjek hvert 30. sekund)

SEEN_FILE = "seen.json"

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


# =====================
# EMAIL
# =====================

def send_email(subject, body):

    if not SENDGRID_API_KEY or not FROM_EMAIL:
        print("❌ Mangler SendGrid credentials")
        return

    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=FROM_EMAIL,
        subject=subject,
        plain_text_content=body
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)

        print("📧 Mail sendt! Status:", response.status_code)

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

        links = soup.find_all("a", href=True)

        found_new = False

        for link_tag in links:

            text = link_tag.get_text().lower()
            href = link_tag["href"]

            # Spring reserverede over
            if "reserveret" in text:
                continue

            if not href.startswith("/"):
                continue

            if "/bolig" not in href:
                continue

            full_url = "https://kerebyudlejning.dk" + href

            if full_url not in seen:

                seen.add(full_url)
                save_seen(seen)

                found_new = True

                print("🏠 NY LEJLIGHED:", full_url)

                send_email(
                    "🏠 Ny lejlighed på Kereby!",
                    f"Der er fundet en ny lejlighed:\n\n{full_url}"
                )

        if not found_new:
            print("Ingen nye lejligheder")

    except Exception as e:
        print("❌ Fejl:", e)


# =====================
# MAIN
# =====================

print("🤖 Kereby-bot startet")

# Test-mail ved opstart
send_email(
    "✅ Kereby-bot startet",
    "Hvis du får denne mail, virker botten korrekt 👍"
)


while True:

    check_site()
    time.sleep(CHECK_INTERVAL)
