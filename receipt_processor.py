import os
import io
from PIL import Image
import sys
import hashlib
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional
from urllib3.util.retry import Retry
import requests
from requests.adapters import HTTPAdapter
import json
from config import load_config

config = load_config()

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
API_URL = "https://proverkacheka.com/api/v1/check/get"
REQUEST_TIMEOUT = 30  # seconds

# Initialize session
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET", "POST"])
session.mount("https://", HTTPAdapter(max_retries=retries))
session.mount("http://", HTTPAdapter(max_retries=retries))


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


def format_receipt_response(resp: dict) -> str:
    """Format the API response into a human-readable string."""
    code = resp.get("code")
    if code != 1 or not resp.get("data"):
        return json.dumps(resp, ensure_ascii=False, indent=2)

    data = resp.get("data")
    j = data.get("json") or data.get("data") or {}
    if not isinstance(j, dict):
        return json.dumps(resp, ensure_ascii=False, indent=2)

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
        item_id = f"id_{h.hexdigest()}"

        recps_items.append(ReceiptItem(name=item_name, price=item_price, id=item_id))

    receipt = Receipt(date=expense_date, store_inn=inn, total_price=total_sum, items=recps_items)
    print(receipt)
    return str(receipt)

def process_receipt(image: io.BytesIO) -> str:
    """Process a receipt image and return the formatted response."""
    token = config.get('proverkacheka_api_key')
    if not token:
        return "API token is required. Set PROVERKACHEKA_TOKEN environment variable."

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
        return f"Error processing receipt: {e}"