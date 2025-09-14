#!/usr/bin/env python3
import io
import os
import json
import sys
import threading
import hashlib
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import telebot
import requests
from flask import Flask, request, render_template
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dataclasses import dataclass
from typing import List


@dataclass
class ReceiptItem:
    name: str
    price: float
    id: str

@dataclass
class Receipt:
    date: str
    total_price: float
    items: List[ReceiptItem]
    store_inn: Optional[int] = None


# Conditional imports for QR decoding
USE_PYZBAR = False
USE_OPENCV = False

try:
    from pyzbar.pyzbar import decode as zbar_decode
    USE_PYZBAR = True
except Exception as e:
    print(f"pyzbar unavailable or can't find zbar native lib: {e}")
    print("Falling back to OpenCV if available...")
    try:
        import cv2
        import numpy as np
        USE_OPENCV = True
    except Exception as e:
        print(f"OpenCV unavailable: {e}")
        print("Please install either pyzbar (plus system zbar) or opencv-python.")
        sys.exit(2)

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
API_URL = "https://proverkacheka.com/api/v1/check/get"
OLLAMA_MODEL = "gpt-oss"
# OLLAMA_MODEL = "deepseek-r1"
REQUEST_TIMEOUT = 30  # seconds

# Initialize bot, Flask, and session
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"])
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))

# Load system prompt
try:
    with Path('system_prompt.txt').open('r', encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read()
except FileNotFoundError:
    print("Error: system_prompt.txt not found.")
    sys.exit(1)


def decode_qr_from_image(image: io.BytesIO) -> List[str]:
    """Decode QR codes from an image, returning a list of decoded strings."""
    try:
        img = Image.open(image).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return []

    if USE_PYZBAR:
        decoded = zbar_decode(img)
        return [d.data.decode("utf-8", errors="ignore") for d in decoded] if decoded else []

    if USE_OPENCV:
        arr = np.array(img)
        arr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        qr_decoder = cv2.QRCodeDetector()
        texts = []
        try:
            retval, decoded_info, points, _ = qr_decoder.detectAndDecodeMulti(arr)
            if retval and decoded_info:
                texts.extend(s for s in decoded_info if s)
        except Exception:
            try:
                data, points = qr_decoder.detectAndDecode(arr)[:2]
                if data:
                    texts.append(data)
            except Exception:
                pass
        return texts

    return []


def post_qrraw(qrraw: str, token: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """Send QR raw data to the API."""
    try:
        resp = session.post(API_URL, data={"token": token, "qrraw": qrraw}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        print(f"HTTP error calling API: {e}")
        print(f"Server response: {e.response.text}")
        raise
    except Exception as e:
        print(f"Error calling API: {e}")
        raise


def post_qrfile(fileobj: io.BytesIO, token: str, filename: str = "qr.jpg", timeout: int = REQUEST_TIMEOUT) -> dict:
    """Upload image file to the API."""
    try:
        files = {"qrfile": (filename, fileobj, "application/octet-stream")}
        resp = session.post(API_URL, data={"token": token}, files=files, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as e:
        print(f"HTTP error calling API: {e}")
        print(f"Server response: {e.response.text}")
        raise
    except Exception as e:
        print(f"Error calling API: {e}")
        raise


def format_receipt_response(resp: dict) -> tuple[int, str]:
    """Format the API response into a human-readable string."""
    code = resp.get("code")
    if code != 1 or not resp.get("data"):
        return 0, json.dumps(resp, ensure_ascii=False, indent=2)

    data = resp.get("data")
    j = data.get("json") or data.get("data") or {}
    if not isinstance(j, dict):
        return 0, json.dumps(resp, ensure_ascii=False, indent=2)
    
    recps_items = []

    inn = j.get('userInn')
    expense_date = j.get('dateTime')
    total_sum = round(j.get('totalSum') / 100, 2)

    for item in j.get("items", []):
        h = hashlib.blake2b(digest_size=8)
        curr_time = datetime.now()
        item_name = item['name']
        item_price = round(item['price'] / 100, 2)

        h.update(f"{item_name}:{item_price}:{curr_time}".encode())
        item_id = h.hexdigest()

        recps_items.append(ReceiptItem(name=item_name, price=item_price, id=item_id))
    
    receipt = Receipt(date=expense_date, store_inn=inn, total_price=total_sum, items=recps_items)
    print(receipt)
    return(receipt)

"""
    text_response = []
    text_response.append(f"Organization: ИНН {j.get('userInn')} {j.get('user') or j.get('org') or ''}")
    text_response.append(f"Address: {j.get('metadata', {}).get('address')}")
    text_response.append(f"Date: {j.get('dateTime')}")
    text_response.append(f"Total: {j.get('totalSum') / 100:.2f}")
    text_response.append(f"Items count: {len(j.get('items', []))}")
    text_response.append("Items:")
    for item in j.get("items", []):
        name = item["name"]
        price = item["price"] / 100
        quantity = item.get("quantity", 1)
        for _ in range(int(quantity)):
            text_response.append(f"{name} — {price:.2f}")
    print("\n".join(text_response))
    return 1, "\n".join(text_response[6:])
"""

def process_receipt(image: io.BytesIO) -> tuple[int, str]:
    """Process a receipt image and return the formatted response."""
    token = os.getenv("PROVERKACHEKA_TOKEN")
    if not token:
        return 0, "API token is required. Set PROVERKACHEKA_TOKEN environment variable."

    qr_texts = decode_qr_from_image(image)
    try:
        if qr_texts:
            print(f"Found {len(qr_texts)} QR code(s). Using first for qrraw.")
            print(f"Decoded qrraw: {qr_texts[0]}")
            response = post_qrraw(qr_texts[0], token)
        else:
            print("No QR detected in image. Uploading as qrfile.")
            image.seek(0)  # Reset file pointer
            response = post_qrfile(image, token)
        return format_receipt_response(response)
    except Exception as e:
        return 0, f"Error processing receipt: {e}"


def ask_ollama(user_message: str, system_prompt: str = SYSTEM_PROMPT, temperature: float = 0.0) -> str:
    """Send a chat request to the Ollama API and return the model's response."""
    try:
        import ollama
        result = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            options={"temperature": temperature},
            think=False,
            stream=False,
        )
        return result["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Error talking to Ollama: {e}"

@app.route("/", methods=["GET", "POST"])
def index():
    """Handle Flask web interface for interacting with Ollama."""
    response_text = ""
    temperature = 0.0
    user_message = ""
    system_prompt = SYSTEM_PROMPT
    ollama_model = OLLAMA_MODEL

    if request.method == "POST":
        system_prompt = request.form.get("system_prompt", system_prompt)
        temperature = float(request.form.get("temperature", temperature))
        user_message = request.form.get("user_message", "").strip()

        if user_message:
            response_text = ask_ollama(user_message, system_prompt, temperature)

    return render_template(
        "index.html",
        response=response_text,
        system_prompt=system_prompt,
        temperature=temperature,
        last_user_message=user_message,
        ollama_model=ollama_model,
    )


@bot.message_handler(content_types=["photo"])
def process_image(message):
    """Handle incoming Telegram photo messages with QR codes."""
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_info.file_path}"
        response = session.get(file_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        image_file = io.BytesIO(response.content)
        image_file.name = "image.png"

        status, result = process_receipt(image_file)
        if status == 1:
            bot.send_message(chat_id=message.chat.id, reply_to_message_id=message.id, text=result)
        else:
            bot.reply_to(message, f"Receipt API Fail:\n{result}")
    except Exception as e:
        bot.reply_to(message, f"Error: {e}")


def run_flask():
    """Run the Flask server."""
    app.run(host="0.0.0.0", port=8080, debug=False)


def run_bot():
    """Run the Telegram bot with polling."""
    bot.infinity_polling(timeout=10, long_polling_timeout=5)


if __name__ == "__main__":
    print("Starting Bot and Flask server...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    run_bot()