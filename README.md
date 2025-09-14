ReceiptVision
ReceiptVision is a Python application that combines a Telegram bot and a Flask web interface to process receipt QR codes and interact with the Ollama AI model. The bot decodes QR codes from receipt images and queries the Proverkacheka API to extract details. The Flask interface allows text-based interaction with the Ollama AI.
Features

Telegram bot for scanning receipt QR codes and retrieving details.
Flask web interface for querying the Ollama AI model.
Supports pyzbar or opencv-python for QR code decoding.
Queries Proverkacheka API for receipt data (e.g., items, total).
Runs bot and web server concurrently.

Prerequisites

Python 3.8+
Telegram bot token (from BotFather)
Proverkacheka API token (set as PROVERKACHEKA_TOKEN)
Ollama server running locally with the gpt-oss model

Installation

Clone the Repository:
git clone https://github.com/yourusername/receipt-vision.git
cd receipt-vision


Install Dependencies:
pip install python-telegram-bot flask requests pillow pyzbar opencv-python ollama

Install either pyzbar (requires libzbar0) or opencv-python:

Ubuntu/Debian: sudo apt-get install libzbar0
macOS: brew install zbar


Set Environment Variables:
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export PROVERKACHEKA_TOKEN="your_proverkacheka_api_token"


Create System Prompt:Create system_prompt.txt in the project root. Example:
You are a helpful assistant providing concise responses.


Run Ollama Server:Follow Ollama documentation to run the server with the gpt-oss model.


Usage

Run the Application:
python main.py

Starts the Telegram bot and Flask server (http://localhost:8080).

Telegram Bot:

Add the bot to Telegram using the token.
Send a receipt image with a QR code.
Receive formatted receipt details (e.g., organization, items, total).


Flask Web Interface:

Visit http://localhost:8080.
Enter a message to query the Ollama AI and view the response.



Project Structure
receipt-vision/
├── main.py              # Main application script
├── system_prompt.txt    # Ollama system prompt
├── templates/
│   └── index.html       # Flask web interface template
└── README.md            # This file

Configuration

Environment Variables:
TELEGRAM_BOT_TOKEN: Telegram bot token.
PROVERKACHEKA_TOKEN: Proverkacheka API token.


Constants (in main.py):
API_URL: https://proverkacheka.com/api/v1/check/get
OLLAMA_MODEL: gpt-oss
REQUEST_TIMEOUT: 30 seconds



Troubleshooting

QR Code Issues: Ensure the image has a valid QR code and pyzbar or opencv-python is installed.
Ollama Errors: Verify the Ollama server is running and the gpt-oss model is available.
Token Errors: Check TELEGRAM_BOT_TOKEN and PROVERKACHEKA_TOKEN are set.

Contributing

Fork the repository.
Create a branch: git checkout -b feature/your-feature.
Commit changes: git commit -m 'Add feature'.
Push: git push origin feature/your-feature.
Open a pull request.

License
MIT License. See LICENSE for details.