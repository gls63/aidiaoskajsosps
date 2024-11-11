import os
import requests
import zipfile
from io import BytesIO
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from telegram.ext.dispatcher import run_async
from telegram.constants import ParseMode
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

def download_pack(update: Update, context):
    url = update.message.text.strip()
    if not url.startswith("https://t.me/addstickers/"):
        update.message.reply_text("Неверная ссылка на пак эмодзи! Используйте ссылку вида: https://t.me/addstickers/...")
        return

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status() 

        pack_name = url.split("/")[3]

        with zipfile.ZipFile(BytesIO(), "w") as zip_file:
            for file_url in response.text.splitlines():
                if not file_url.startswith("https://"):
                    continue

                file_response = requests.get(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                file_response.raise_for_status()

                zip_file.writestr(f"{pack_name}/{os.path.basename(file_url)}", file_response.content)

        zip_file.seek(0)
        update.message.reply_document(zip_file, filename=f"{pack_name}.zip", caption=f"Пак эмодзи скачан! Скачать?")

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Верно", callback_data=f"download_{pack_name}")]
        ])
        update.message.reply_text("Нажмите \"Верно\", чтобы скачать файл с эмодзи", reply_markup=keyboard)

    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"Ошибка при скачивании: {e}")

@run_async
def download_callback(update: Update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("download_"):
        pack_name = data.split("_")[1]

        # Отправка файла с эмодзи
        with open(f"{pack_name}.zip", 'rb') as file:
            query.message.reply_document(file, filename=f"{pack_name}.zip", caption=f"Пак эмодзи отправлен!")
        os.remove(f"{pack_name}.zip") 

    query.answer()

updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

dispatcher.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("Привет! Отправьте мне ссылку на Telegram-пак с эмодзи.")))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_pack))
dispatcher.add_handler(CallbackQueryHandler(download_callback))

updater.start_polling()
updater.idle()