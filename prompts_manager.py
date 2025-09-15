import os

PROMPTS_DIR = 'prompts'

def list_prompts():
    if not os.path.exists(PROMPTS_DIR):
        os.makedirs(PROMPTS_DIR)
    return [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.txt')]

def load_prompt(filename):
    path = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r') as f:
            return f.read()
    return ""

def save_prompt(filename, content):
    path = os.path.join(PROMPTS_DIR, filename)
    with open(path, 'w') as f:
        f.write(content)