from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import asyncio
import os
import json
import datetime

# === Flask-приложение ===
app = Flask(__name__)

# === Переменная для Telegram App ===
telegram_app = None

users_file = "data/users.json"
os.makedirs("data", exist_ok=True)

# Загрузка пользователей
def load_users():
    try:
        with open(users_file, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохранение пользователей
def save_users(users):
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

# Telegram-хендлеры
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
        await update.message.reply_text("📍 Адрес сохранён! Ваша подписка активирована.")
    else:
        await update.message.reply_text("Напишите /start чтобы выбрать тариф.")

# Инициализация Telegram
async def init_telegram():
    global telegram_app
    telegram_app = ApplicationBuilder().token(os.environ["BOT_TOKEN"]).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(button))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.bot.set_webhook(url=os.environ["WEBHOOK_URL"])

# Flask Webhook (БЕЗ await!)
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json()
        update = Update.de_json(data, telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))
        return "ok", 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500

# При старте — запускаем Telegram-бота
@app.before_first_request
def activate_bot():
    asyncio.get_event_loop().create_task(init_telegram())

# Стартовое приложение для Render
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
