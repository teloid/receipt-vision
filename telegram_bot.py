from telegram import Update
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import load_config
from receipt_processor import process_receipt
from llm_handler import categorize_receipt


async def handle_photo(update: Update, context):
    photo = await update.message.photo[-1].get_file()
    photo_path = 'temp_receipt.jpg'
    await photo.download_to_drive(photo_path)

    try:
        receipt_data = process_receipt(photo_path)
        categorized = categorize_receipt(receipt_data)
        await update.message.reply_text(f"Categorized: {categorized}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
    finally:
        os.remove(photo_path)  # Clean up


def run_bot():
    print('Bot is running!')
    config = load_config()
    print(config)
    token = config['telegram_bot_token']
    app = Application.builder().token(token).build()
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()