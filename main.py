import os
import requests
import zipfile
from io import BytesIO
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler
from telegram.ext.filters import Filters
from telegram.ext.dispatcher import run_async
from telegram.constants import ParseMode
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup


# Токен вашего бота
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


# Функция для скачивания пака эмодзи
def download_pack(update: Update, context):
    url = update.message.text.strip()
    if not url.startswith("https://t.me/addstickers/"):
        update.message.reply_text("Неверная ссылка на пак эмодзи! Используйте ссылку вида: https://t.me/addstickers/...")
        return

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status() # Проверка кода ответа

        # Извлечение имени пакета из ссылки
        pack_name = url.split("/")[3]

        # Создание zip-архива
        with zipfile.ZipFile(BytesIO(), "w") as zip_file:
            for file_url in response.text.splitlines():
                if not file_url.startswith("https://"):
                    continue

                # Скачивание файла
                file_response = requests.get(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                file_response.raise_for_status()

                # Добавление файла в архив
                zip_file.writestr(f"{pack_name}/{os.path.basename(file_url)}", file_response.content)

        zip_file.seek(0)
        update.message.reply_document(zip_file, filename=f"{pack_name}.zip", caption=f"Пак эмодзи скачан! Скачать?")

        # Кнопка "Верно" для отправки файла
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Верно", callback_data=f"download_{pack_name}")]
        ])
        update.message.reply_text(
            "Нажмите \"Верно\", чтобы скачать файл с эмодзи", reply_markup=keyboard
        )

    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"Ошибка при скачивании: {e}")


# Функция обработки нажатия на кнопку "Верно"
@run_async
def download_callback(update: Update, context):
    query = update.callback_query
    data = query.data

    if data.startswith("download_"):
        pack_name = data.split("_")[1]

        # Отправка файла с эмодзи
        with open(f"{pack_name}.zip", "rb") as file:
            query.message.reply_document(
                file, filename=f"{pack_name}.zip", caption=f"Пак эмодзи отправлен!"
            )
        os.remove(f"{pack_name}.zip") # Удаление временного файла

    query.answer()


# Функция для показа меню
def show_menu(update: Update, context):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Скачать пак эмодзи", callback_data="download_pack"),
                InlineKeyboardButton("Помощь", callback_data="help"),
            ]
        ]
    )
    update.message.reply_text(
        "👋 Привет! Что вы хотите сделать?", reply_markup=keyboard
    )


# Функция для показа справки
def show_help(update: Update, context):
    update.message.reply_text(
        "Я могу скачивать пакеты эмодзи с Telegram! Отправьте мне ссылку на пак в формате `https://t.me/addstickers/...`."
    )


# Функция обработки нажатия на кнопки меню
@run_async
def menu_callback(update: Update, context):
    query = update.callback_query
    data = query.data

    if data == "download_pack":
        query.message.reply_text("Отправьте мне ссылку на пак эмодзи.")
    elif data == "help":
        show_help(update, context)

    query.answer()


# Создание объекта Updater
updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

# Добавление обработчиков
dispatcher.add_handler(CommandHandler("start", show_menu))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, download_pack))
dispatcher.add_handler(CallbackQueryHandler(download_callback))
dispatcher.add_handler(CallbackQueryHandler(menu_callback, pattern="^download_pack$|^help$"))

# Запуск бота
updater.start_polling()
updater.idle()