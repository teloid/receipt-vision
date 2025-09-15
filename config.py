import json
import os

CONFIG_FILE = 'config.json'
PROMPTS_DIR = 'prompts'

DEFAULT_CONFIG = {
    'llm_provider': 'chatgpt',  # 'ollama' or 'chatgpt'
    'ollama_model': 'gpt-4o-mini',  # model 'gpt-oss' or 'gpt-4o-mini'
    'openai_api_key': os.getenv('OPENAI_API_KEY'),      # Set via Streamlit or env
    'temperature': 0.0,
    'proverkacheka_api_key': os.getenv('PROVERKACHEKA_TOKEN'),  # If needed
    'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),   # Set via env for security
    'default_prompt': os.path.join(PROMPTS_DIR, 'receipt_processor.txt')
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG