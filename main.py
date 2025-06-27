from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, ContextTypes, filters
import os
import json
import datetime
import asyncio

app = Flask(__name__)
bot = Bot(token=os.environ["BOT_TOKEN"])

users_file = "data/users.json"

# Функции для работы с пользователями
def load_users():
    try:
        with open(users_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Базовый — 199 руб/мес", callback_data='tarif_199')],
        [InlineKeyboardButton("Стандарт — 299 руб/мес", callback_data='tarif_299')],
        [InlineKeyboardButton("Премиум — 399 руб/мес", callback_data='tarif_399')],
        [InlineKeyboardButton("Связаться с мастером", url="https://t.me/T1m11333")]
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 Привет! Я — мастер по ремонту бытовой техники из Новомосковска.\n\nВыберите тариф подписки:", reply_markup=markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tarif_map = {
        'tarif_199': "Базовый — 199 руб/мес",
        'tarif_299': "Стандарт — 299 руб/мес",
        'tarif_399': "Премиум — 399 руб/мес"
    }
    tarif = tarif_map.get(query.data, "Неизвестный тариф")
    user_id = str(query.from_user.id)
    users = load_users()
    users[user_id] = {
        "username": query.from_user.username,
        "tarif": tarif,
        "subscribed_at": str(datetime.date.today())
    }
    save_users(users)
    await query.edit_message_text(f"✅ Вы выбрали тариф: {tarif}\n\nПожалуйста, отправьте ваш точный адрес одним сообщением.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_users()
    if user_id in users and "address" not in users[user_id]:
        users[user_id]["address"] = update.message.text
        save_users(users)
        await update.message.reply_text("📍 Адрес сохранён! Ваша подписка активирована.")
    else:
        await update.message.reply_text("Напишите /start, чтобы выбрать тариф.")

# Webhook обработчик
@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    asyncio.run(application.process_update(update))
    return 'ok'

# Telegram application
application = Application.builder().token(os.environ["BOT_TOKEN"]).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Установка webhook при запуске
@app.before_request
def setup_webhook():
    webhook_url = os.environ["WEBHOOK_URL"]
    asyncio.run(bot.set_webhook(url=webhook_url))

# Gunicorn ищет переменную "app"
if __name__ == "__main__":
    app.run(port=10000)
