from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import datetime

users_file = "data/users.json"

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

# Обработка старта
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
# Обработка выбора тарифа
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
    await query.edit_message_text(f"✅ Вы выбрали тариф: {tarif}

Пожалуйста, отправьте ваш адрес одним сообщением.")

# Сбор адреса
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    users = load_users()
    if user_id in users and "address" not in users[user_id]:
        users[user_id]["address"] = update.message.text
        save_users(users)
        await update.message.reply_text("📍 Адрес сохранён! Ваша подписка активирована. При необходимости свяжитесь со мной через кнопку в меню.")
    else:
        await update.message.reply_text("Напишите /start чтобы выбрать тариф.")

# Запуск бота
def main():
    app = ApplicationBuilder().token("1597117287:AAFKfS8zYbSxLACyoWGfkdm783CKTjXe3_0").build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
