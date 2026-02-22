import re
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- TELEGRAM API ----------------

api_id = 37734548
api_hash = "dc229a7f5288f2338cb5ec7d5830e0b1"

SESSION = "YOUR_STRING_SESSION_HERE"

client = TelegramClient(StringSession(SESSION), api_id, api_hash)

# ---------------- SOURCE CHANNELS ----------------

source_chats = [
    "lootversemen",
    "lootversewomen",
    "sheinxpress",
    "TufanLoots",
    "sheinstock_rohan_notify_bot"
]

# ---------------- DESTINATION ----------------

destination_chat = "rohan_shein"

TOTAL_STOCK_LIMIT = 10
DUPLICATE_TIME = 600  # 10 minutes

sent_links = {}

# ---------------- CLEAN MESSAGE ----------------

def clean_message(text):
    if not text:
        return ""

    skip_words = [
        "Voucher",
        "Buy Vouchers",
        "Coupon",
        "Free ₹",
        "Group And Info"
    ]

    lines = text.split("\n")
    return "\n".join([l for l in lines if not any(w.lower() in l.lower() for w in skip_words)])

# ---------------- LINK DETECTION ----------------

def extract_shein_link(text):
    if not text:
        return None
    match = re.search(r'https?://\S*shein\S+', text)
    return match.group(0) if match else None

# ---------------- CHECK OUT POSTS ----------------

def is_check_out_shein_post(text):
    return "check out shein on shein" in text.lower()

# ---------------- FINAL BULLETPROOF STOCK DETECTOR ----------------

def total_stock(text):
    if not text:
        return 0

    # 🔧 NORMALIZE TELEGRAM FORMATTING
    text = text.replace('\xa0', ' ')
    text = text.replace('–', '-')
    text = text.replace('—', '-')

    text_upper = text.upper()

    total = 0

    # 1️⃣ Numeric sizes → 32 : 19
    matches = re.findall(r'\d+\s*:\s*(\d+)', text_upper)
    total += sum(int(num) for num in matches)

    # 2️⃣ Letter sizes → S : 24 , XXL : 29
    matches2 = re.findall(r'(?:XS|S|M|L|XL|XXL|XXXL)\s*:\s*(\d+)', text_upper)
    total += sum(int(num) for num in matches2)

    # 3️⃣ Bracket sizes → M(5)
    matches3 = re.findall(r'[A-Z]+\(\s*(\d+)\s*\)', text_upper)
    total += sum(int(num) for num in matches3)

    # 4️⃣ ONE SIZE → ONE SIZE : 12
    matches4 = re.findall(r'ONE SIZE[^\d]*(\d+)', text_upper)
    total += sum(int(num) for num in matches4)

    return total

# ---------------- DUPLICATE FILTER ----------------

def is_duplicate(link):
    now = time.time()

    if link in sent_links:
        if now - sent_links[link] < DUPLICATE_TIME:
            return True

    sent_links[link] = now
    return False

# ---------------- MAIN HANDLER ----------------

@client.on(events.NewMessage(chats=source_chats))
async def handler(event):

    if event.is_private:
        return

    message_text = event.message.message

    if not message_text:
        return

    shein_link = extract_shein_link(message_text)

    if not shein_link:
        return

    # Duplicate check
    if is_duplicate(shein_link):
        print("Duplicate skipped")
        return

    cleaned_text = clean_message(message_text)

    # Rule 1: Checkout posts instant send
    if is_check_out_shein_post(message_text):
        send = True
    else:
        stock_sum = total_stock(message_text)
        print("STOCK DETECTED =", stock_sum)
        send = stock_sum >= TOTAL_STOCK_LIMIT

    if not send:
        print("Skipped low stock")
        return

    try:
        if event.message.photo:
            file = await event.message.download_media()
            sent = await client.send_file(destination_chat, file, caption=cleaned_text)
        else:
            sent = await client.send_message(destination_chat, cleaned_text)

        print("⚡ ALERT SENT")

        # Auto pin
        try:
            await client.pin_message(destination_chat, sent.id, notify=False)
            print("📌 pinned")
        except:
            print("Pin failed")

    except Exception as e:
        print("Error:", e)

print("⚡ PRO SHEIN BOT RUNNING...")

client.start()
client.run_until_disconnected()
