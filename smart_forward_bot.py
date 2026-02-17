import re
import time
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- TELEGRAM API ----------------

api_id = 37734548
api_hash = "dc229a7f5288f2338cb5ec7d5830e0b1"

SESSION = "1BVtsOLoBu0FrcP9rmRhWo_xfa4ngHGMdCdzIfeRc9cQbQI7RY218jn-QQPH0YJ9XQ0hMz2Sco1u8N3V7iWT9_LhM8ZLt5yAku5d5tBNeBJ2G5OeYaMwzCzN_XrNVjya2jDFWvJEZ08Hc4Lxr99ssAqCAk3c2ISSrrU1XYqPFF7FXAWHF2qQjAKEyyQ2NZJXQdya5jF3qRg7YOLnVyklpeshjLPcp7SJuFSS4xEbOpMnGuJwON4ub_LHlP1mu5a6zN2rxny9I6C-5Wsh9ajoN1OXDJ6V8NNQ8vAQgimc3K45Ig7T8IdBzBNBNnGBixdvqR240HWdBXcNwMTFCuYwrbOIa5YPgCaI="


client = TelegramClient(StringSession(SESSION), api_id, api_hash)

# ---------------- SOURCE CHANNELS ----------------

source_chats = [
    "lootversemen",
    "lootversewomen",
    "sheinxpress",
    "TufanLoots"
]

# ---------------- DESTINATION ----------------

destination_chat = "rohan_shein"

TOTAL_STOCK_LIMIT = 10
DUPLICATE_TIME = 300

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


# ---------------- EXTRACT SHEIN LINK ----------------

def extract_shein_link(text):
    match = re.search(r'https://(www\.)?sheinindia\.in/p/\d+', text)
    return match.group(0) if match else None


# ---------------- CHECK NEW DROP ----------------

def is_check_out_shein_post(text):
    return "check out shein on shein" in text.lower()


# ---------------- SAFE STOCK DETECTION ----------------

def total_stock(text):

    text_upper = text.upper()
    total = 0

    # detect ONLY size lines
    size_lines = re.findall(
        r'(SIZE.*?:\s*\d+|XS.*?:\s*\d+|S.*?:\s*\d+|M.*?:\s*\d+|L.*?:\s*\d+|XL.*?:\s*\d+|XXL.*?:\s*\d+|XXXL.*?:\s*\d+|ONE SIZE.*?:\s*\d+)',
        text_upper
    )

    for line in size_lines:
        match = re.search(r':\s*(\d+)', line)
        if match:
            total += int(match.group(1))

    return total


# ---------------- DUPLICATE FILTER ----------------

def is_duplicate(link):
    now = time.time()

    if link in sent_links:
        if now - sent_links[link] < DUPLICATE_TIME:
            return True

    sent_links[link] = now
    return False


# ---------------- FORMAT MESSAGE ----------------

def format_message(text, is_men=False, is_women=False):

    cleaned = clean_message(text)

    if is_men:
        header = "🔥 MEN PRIORITY STOCK\nAs Shein Stock Alert Rohan\n\n"
    elif is_women:
        header = "👗 WOMEN PRIORITY STOCK\nAs Shein Stock Alert Rohan\n\n"
    else:
        header = "🚨 SHEIN STOCK ALERT\nAs Shein Stock Alert Rohan\n\n"

    return header + cleaned


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

    # duplicate filter
    if is_duplicate(shein_link):
        print("Duplicate skipped")
        return

    # detect channel type
    chat_name = str(event.chat.username).lower()

    is_men = chat_name == "lootversemen"
    is_women = chat_name == "lootversewomen"

    # sending logic
    if is_check_out_shein_post(message_text):
        send = True
    else:
        stock_sum = total_stock(message_text)
        send = stock_sum >= TOTAL_STOCK_LIMIT

    if not send:
        print("Skipped low stock")
        return

    final_text = format_message(message_text, is_men, is_women)

    try:
        if event.message.photo:
            file = await event.message.download_media()
            await client.send_file(destination_chat, file, caption=final_text)
        else:
            await client.send_message(destination_chat, final_text)

        print("⚡ ALERT SENT")

    except Exception as e:
        print("Error:", e)


print("⚡ FINAL STOCK ENGINE RUNNING...")

client.start()
client.run_until_disconnected()
