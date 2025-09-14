# ReceiptVision

ReceiptVision is a Python application combining a Telegram bot and Flask web interface. The bot scans QR codes from receipt images and queries the Proverkacheka API for details. The web interface interacts with the Ollama AI model for text queries.

## Features
- Telegram bot for extracting receipt details from QR codes.
- Flask interface for querying the Ollama AI.
- QR decoding with `pyzbar` or `opencv-python` fallback.
- Concurrent bot and web server operation.

## Prerequisites
- Python 3.8+
- Telegram bot token (from [BotFather](https://t.me/BotFather))
- Proverkacheka API token (`PROVERKACHEKA_TOKEN`)
- Ollama server with `gpt-oss` model

## Installation

1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/receipt-vision.git
   cd receipt-vision
   ```

2. **Install Dependencies**:
   ```bash
   pip install python-telegram-bot flask requests pillow pyzbar opencv-python ollama
   ```
   Install `pyzbar` (requires `libzbar0`) or `opencv-python`:
   - Ubuntu/Debian: `sudo apt-get install libzbar0`
   - macOS: `brew install zbar`

3. **Set Environment Variables**:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
   export PROVERKACHEKA_TOKEN="your_proverkacheka_api_token"
   ```

4. **Create System Prompt**:
   Create `system_prompt.txt` in the project root. Example:
   ```text
   You are a helpful assistant providing concise responses.
   ```

5. **Run Ollama Server**:
   Follow [Ollama documentation](https://ollama.ai/) to run the server with `gpt-oss`.

## Usage

1. **Run Application**:
   ```bash
   python main.py
   ```
   Starts Telegram bot and Flask server (`http://localhost:8080`).

2. **Telegram Bot**:
   - Add bot to Telegram using the token.
   - Send a receipt image with a QR code.
   - Receive receipt details (e.g., items, total).

3. **Flask Interface**:
   - Visit `http://localhost:8080`.
   - Enter a message to query Ollama AI.

## Project Structure

```plaintext
receipt-vision/
├── main.py              # Main application script
├── system_prompt.txt    # Ollama system prompt
├── templates/
│   └── index.html       # Flask web interface template
└── README.md            # This file
```

## Configuration
- **Environment Variables**:
  - `TELEGRAM_BOT_TOKEN`: Telegram bot token.
  - `PROVERKACHEKA_TOKEN`: Proverkacheka API token.
- **Constants** (in `main.py`):
  - `API_URL`: `https://proverkacheka.com/api/v1/check/get`
  - `OLLAMA_MODEL`: `gpt-oss`
  - `REQUEST_TIMEOUT`: 30 seconds

## Troubleshooting
- **QR Code Issues**: Ensure valid QR code and `pyzbar` or `opencv-python` installed.
- **Ollama Errors**: Verify Ollama server and `gpt-oss` model are running.
- **Token Errors**: Check `TELEGRAM_BOT_TOKEN` and `PROVERKACHEKA_TOKEN`.

## Contributing
1. Fork the repository.
2. Create a branch: `git checkout -b feature/your-feature`.
3. Commit: `git commit -m 'Add feature'`.
4. Push: `git push origin feature/your-feature`.
5. Open a pull request.

## License
MIT License. See [LICENSE](LICENSE) for details.