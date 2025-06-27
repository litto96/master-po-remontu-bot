import os
import json
import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, ContextTypes, filters
)
import asyncio

# Подготовка
app = Flask(__name__)
telegram_app: Application = None  # инициализируется позже

users_file = "data/users.json"
os.makedirs("data", exist_ok=True)

# Загрузка и сохранение пользователей
def load_users():
    try:
        with open(users_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users):
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

# Хэндлеры Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Базовый — 199 руб/мес", callback_data='tarif_199')],
        [InlineKeyboardButton("Стандарт — 299 руб/мес", callback_data='tarif_299')],
        [InlineKeyboardButton("Премиум — 399 руб/мес", callback_data='tarif_399')],
        [InlineKeyboardButton("Связаться с мастером", url="https://t.me/T1m11333")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Я — мастер по ремонту бытовой техники из Новомосковска.\n\n"
        "Выберите тариф подписки:",
        reply_markup=reply_markup
    )

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
    await query.edit_message_text(
        f"✅ Вы выбрали тариф: {tarif}\n\n"
        "Пожалуйста, отправьте ваш точный адрес одним сообщением."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_users()
    if user_id in users and "address" not in users[user_id]:
        users[user_id]["address"] = update.message.text
        save_users(users)
        await update.message.reply_text("📍 Адрес сохранён! Ваша подписка активирована. При необходимости свяжитесь со мной через кнопку в меню.")
    else:
        await update.message.reply_text("Напишите /start чтобы выбрать тариф.")

# Flask-обработчик Webhook
@app.route("/webhook", methods=["POST"])
async def webhook():
    data = request.get_json()
    if telegram_app:
        update = Update.de_json(data, telegram_app.bot)
        await telegram_app.process_update(update)
    return "ok", 200

# Запуск Telegram и Flask
async def run():
    global telegram_app
    telegram_app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/webhook")
    await telegram_app.start()
    print("🤖 Telegram bot started")

# Flask старт
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(run())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
