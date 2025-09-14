# --- LLM helpers -------------------------------------------------------------
# pip install openai
import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

# Если хочешь хранить несколько system prompt'ов в файлах ./prompts/<name>.txt
PROMPTS_DIR = Path("prompts")

@lru_cache
def load_prompt(prompt_name: str) -> str:
    """Читает текст промпта из ./prompts/<prompt_name>.txt"""
    p = PROMPTS_DIR / f"{prompt_name}.txt"
    if not p.exists():
        raise FileNotFoundError(f"Prompt file not found: {p}")
    return p.read_text(encoding="utf-8")

def pick_text_or_file(system_prompt: str) -> str:
    """
    Удобный трюк: если system_prompt выглядит как 'file:имя',
    прочитать prompts/имя.txt; иначе трактовать как сырой текст.
    """
    if system_prompt.startswith("file:"):
        return load_prompt(system_prompt.split(":", 1)[1])
    return system_prompt


# можно переопределять через переменные окружения
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")   # дешёвый и быстрый
# OLLAMA_MODEL уже есть у тебя в коде

# --- OLLAMA ------------------------------------------------------------------
def ask_ollama(user_message: str,
               system_prompt: str,
               temperature: float = 0.0,
               model: Optional[str] = None) -> str:
    """Запрос к локальному Ollama."""
    try:
        import ollama
        used_model = model or OLLAMA_MODEL
        result = ollama.chat(
            model=used_model,
            messages=[
                {"role": "system", "content": pick_text_or_file(system_prompt)},
                {"role": "user", "content": user_message},
            ],
            options={"temperature": temperature},
            think=False,
            stream=False,
        )
        return (result.get("message", {}) or {}).get("content", "").strip()
    except Exception as e:
        return f"⚠️ Error talking to Ollama: {e}"


# --- OPENAI ------------------------------------------------------------------
def _get_openai_client():
    """
    Ленивое создание клиента OpenAI.
    Уважает OPENAI_API_KEY и (опционально) OPENAI_BASE_URL.
    """
    from openai import OpenAI  # официальная либра OpenAI (>=1.x)
    kwargs = {}
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        kwargs["api_key"] = api_key
    return OpenAI(**kwargs)

def ask_openai(user_message: str,
               system_prompt: str,
               temperature: float = 0.0,
               model: Optional[str] = None) -> str:
    """Запрос к OpenAI Chat Completions (через офиц. SDK)."""
    try:
        client = _get_openai_client()
        used_model = model or OPENAI_MODEL
        resp = client.chat.completions.create(  # Chat Completions поддерживается и сейчас
            model=used_model,
            messages=[
                {"role": "system", "content": pick_text_or_file(system_prompt)},
                {"role": "user", "content": user_message},
            ],
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error talking to OpenAI: {e}"