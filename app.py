import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Создаем Flask приложение
app = Flask(__name__)

# Глобальная переменная для приложения Telegram
telegram_app = None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    user_id = user.id
    
    welcome_text = f"""
👋 Привет, {user.first_name}!

🆔 Твой ID: `{user_id}`

Просто отправь мне любое сообщение, и я покажу твой ID!
    """
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает ID пользователя для любого сообщения"""
    user = update.effective_user
    user_id = user.id
    
    response_text = f"""
📋 Информация о пользователе:

🆔 ID: `{user_id}`
👤 Имя: {user.first_name}
📛 Фамилия: {user.last_name or 'Не указана'}
🔗 Username: @{user.username or 'Не указан'}
    """
    
    await update.message.reply_text(response_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка: {context.error}")

def setup_bot():
    """Настройка бота"""
    global telegram_app
    
    telegram_app = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, show_id))
    telegram_app.add_error_handler(error_handler)
    
    # Настраиваем webhook если на Render
    if os.environ.get('RENDER'):
        webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/webhook"
        telegram_app.bot.set_webhook(webhook_url)
        logger.info(f"Webhook установлен: {webhook_url}")

@app.route('/')
def home():
    return "🤖 Telegram Bot is running! Use /start in Telegram."

@app.route('/ping')
def ping():
    return "pong"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint для webhook"""
    if telegram_app is None:
        return "Bot not initialized", 500
        
    update = Update.de_json(request.get_json(), telegram_app.bot)
    telegram_app.update_queue.put(update)
    return 'ok'

if __name__ == '__main__':
    # Проверяем, что токен установлен
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable is not set!")
    
    # Настраиваем бота
    setup_bot()
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
