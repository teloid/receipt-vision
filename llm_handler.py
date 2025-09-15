import ollama
from openai import OpenAI
from config import load_config
from prompts_manager import load_prompt


def categorize_receipt(data, ):
    config = load_config()
    provider = config['llm_provider']
    temperature = config['temperature']
    system_prompt = load_prompt(config['default_prompt'])

    user_prompt = f"Categorize this receipt data: {data}"  # Customize as needed

    if provider == 'ollama':
        response = ollama.chat(
            model=config['ollama_model'],
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            options={'temperature': temperature}
        )
        return response['message']['content']

    elif provider == 'chatgpt':
        client = OpenAI(api_key=config['openai_api_key'])
        response = client.chat.completions.create(
            model='gpt-4o-mini',  # Or your preferred model
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            temperature=temperature
        )
        return response.choices[0].message.content

    else:
        raise ValueError("Invalid LLM provider")