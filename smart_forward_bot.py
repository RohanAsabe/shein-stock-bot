import re
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ---------------- TELEGRAM API ----------------

api_id = 37734548
api_hash = "dc229a7f5288f2338cb5ec7d5830e0b1"

# ---------------- SOURCE CHANNELS ----------------

source_chats = [
    "lootversemen",
    "lootversewomen",
    "sheinxpress"
]

# ---------------- DESTINATION CHANNEL ----------------

destination_chat = "rohan_shein"

MIN_STOCK = 10

SESSION = "1BVtsOLoBu0FrcP9rmRhWo_xfa4ngHGMdCdzIfeRc9cQbQI7RY218jn-QQPH0YJ9XQ0hMz2Sco1u8N3V7iWT9_LhM8ZLt5yAku5d5tBNeBJ2G5OeYaMwzCzN_XrNVjya2jDFWvJEZ08Hc4Lxr99ssAqCAk3c2ISSrrU1XYqPFF7FXAWHF2qQjAKEyyQ2NZJXQdya5jF3qRg7YOLnVyklpeshjLPcp7SJuFSS4xEbOpMnGuJwON4ub_LHlP1mu5a6zN2rxny9I6C-5Wsh9ajoN1OXDJ6V8NNQ8vAQgimc3K45Ig7T8IdBzBNBNnGBixdvqR240HWdBXcNwMTFCuYwrbOIa5YPgCaI="

client = TelegramClient(StringSession(SESSION), api_id, api_hash)


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


# ---------------- CHECK SHEIN LINK ----------------

def has_shein_link(text):
    return "sheinindia.in/p/" in text.lower()


# ---------------- ACCURATE STOCK DETECTION ----------------

def has_high_stock(text):

    text_upper = text.upper()

    # must contain stock section
    if "SIZES" not in text_upper and "ONE SIZE" not in text_upper:
        return False

    # extract only stock area
    if "SIZES" in text_upper:
        stock_part = text_upper.split("SIZES")[-1]
    else:
        stock_part = text_upper.split("ONE SIZE")[-1]

    # detect numbers only inside stock lines
    matches = re.findall(r':\s*(\d+)', stock_part)

    return any(int(num) > MIN_STOCK for num in matches)


# ---------------- INSTANT HANDLER ----------------

@client.on(events.NewMessage(chats=source_chats))
async def handler(event):

    # ignore personal messages
    if event.is_private:
        return

    # ignore replies
    if event.message.reply_to:
        return

    message_text = event.message.message

    if not message_text:
        return

    # strict conditions
    if not has_shein_link(message_text):
        return

    if not has_high_stock(message_text):
        print("Skipped low stock")
        return

    cleaned_text = clean_message(message_text)

    try:
        # instant send
        if event.message.photo:
            file = await event.message.download_media()
            asyncio.create_task(
                client.send_file(destination_chat, file, caption=cleaned_text)
            )
        else:
            asyncio.create_task(
                client.send_message(destination_chat, cleaned_text)
            )

        print("⚡ INSTANT HIGH STOCK ALERT SENT")

    except Exception as e:
        print("Error:", e)


print("⚡ FINAL INSTANT SHEIN BOT RUNNING...")

client.start()
client.run_until_disconnected()


asyncio.run(main())


