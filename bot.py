import os
import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from site_checker import SiteChecker

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация проверщика сайтов
site_checker = SiteChecker()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        welcome_message = (
            "🛡️ *Добро пожаловать в Site Security Checker Bot!*\n\n"
            "Я профессиональный бот для проверки безопасности сайтов.\n\n"
            "*Что я умею:*\n"
            "✅ Определение IP-адреса и геолокации\n"
            "✅ Анализ WHOIS данных\n"
            "✅ Проверка SSL сертификата\n"
            "✅ Анализ безопасности заголовков\n"
            "✅ Определение фишинговых признаков\n"
            "✅ Проверка по базам мошеннических сайтов\n\n"
            "*Как использовать:*\n"
            "Просто отправьте мне ссылку на сайт (например: https://example.com)"
        )
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = (
            "📖 *Инструкция по использованию:*\n\n"
            "1️⃣ Отправьте URL сайта для проверки\n"
            "2️⃣ Дождитесь результатов анализа\n\n"
            "*Команды:*\n"
            "/start - Начать работу\n"
            "/help - Показать это сообщение\n"
            "/about - О боте\n\n"
            "*Пример:*\n"
            "`https://example.com`"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /about"""
        about_text = (
            "🤖 *Site Security Checker Bot v1.0*\n\n"
            "Профессиональный инструмент для анализа безопасности веб-сайтов.\n\n"
            "*Технологии:*\n"
            "• WHOIS анализ\n"
            "• Геолокация IP\n"
            "• SSL/TLS проверка\n"
            "• Анализ заголовков безопасности\n"
            "• Машинное обучение для детекции фишинга\n"
            "• Интеграция с базами угроз\n\n"
            "*Разработчик:* @your_username\n"
            "*Исходный код:* [GitHub](https://github.com/yourusername/telegram-site-checker-bot)"
        )
        
        await update.message.reply_text(
            about_text,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    
    async def handle_url(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик URL сообщений"""
        url = update.message.text.strip()
        
        # Отправка сообщения о начале проверки
        status_message = await update.message.reply_text(
            "🔍 *Анализирую сайт...*\nПожалуйста, подождите.",
            parse_mode='Markdown'
        )
        
        try:
            # Выполнение проверки
            result = await site_checker.check_site(url)
            
            # Формирование отчета
            report = await self.format_report(result)
            
            # Добавление клавиатуры для действий
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔗 Открыть сайт", url=url),
                    InlineKeyboardButton("📊 Подробный отчет", callback_data=f"detailed_{result['id']}")
                ],
                [
                    InlineKeyboardButton("🚨 Пожаловаться", callback_data=f"report_{result['id']}"),
                    InlineKeyboardButton("🔄 Проверить другой", callback_data="new_check")
                ]
            ])
            
            await status_message.edit_text(
                report,
                parse_mode='Markdown',
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
        except Exception as e:
            logger.error(f"Error checking site {url}: {e}")
            await status_message.edit_text(
                "❌ *Ошибка при проверке сайта*\n\n"
                "Убедитесь, что URL введен корректно и сайт доступен.\n\n"
                f"Ошибка: `{str(e)}`",
                parse_mode='Markdown'
            )
    
    async def format_report(self, result: dict) -> str:
        """Форматирование отчета"""
        # Цветовая индикация риска
        risk_emoji = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'safe': '✅'
        }
        
        risk_color = risk_emoji.get(result['risk_level'], '⚪')
        
        report = f"""
{risk_color} *ОТЧЕТ О ПРОВЕРКЕ САЙТА* {risk_color}

📌 *Основная информация:*
• *URL:* {result['url']}
• *Название сайта:* {result['site_title']}
• *Домен:* {result['domain']}
• *IP-адрес:* `{result['ip_address']}`
• *Геолокация:* {result['location']}
• *Хостинг-провайдер:* {result['hosting_provider']}

🔒 *Безопасность:*
• *SSL сертификат:* {result['ssl_status']}
• *Рейтинг безопасности:* {result['security_score']}/100
• *Вредоносное ПО:* {result['malware_detected']}
• *В черных списках:* {result['blacklisted']}

🎣 *Анализ фишинга:*
• *Вероятность фишинга:* {result['phishing_score']}%
• *Признаки:* {', '.join(result['phishing_indicators']) if result['phishing_indicators'] else 'Не обнаружены'}
• *Подозрительные паттерны:* {result['suspicious_patterns']}

📊 *Дополнительная информация:*
• *Дата регистрации домена:* {result['domain_registration_date']}
• *Срок действия:* {result['domain_expiry_date']}
• *Страна регистрации:* {result['domain_country']}
• *Технологии:* {', '.join(result['technologies'])}
• *Индексация в Google:* {result['google_indexed']}

{'🚨 *ВНИМАНИЕ!* ' + result['warning_message'] if result['warning_message'] else ''}
        """
        
        return report
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик кнопок"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "new_check":
            await query.edit_message_text(
                "📝 Отправьте новый URL для проверки:",
                parse_mode='Markdown'
            )
        elif query.data.startswith("detailed_"):
            # Здесь можно показать более подробный отчет
            await query.edit_message_text(
                "📊 *Детальный отчет будет доступен в следующей версии бота*\n\n"
                "Следите за обновлениями!",
                parse_mode='Markdown'
            )
        elif query.data.startswith("report_"):
            await query.edit_message_text(
                "🚨 *Спасибо за сообщение!*\n\n"
                "Этот сайт будет добавлен в базу для проверки.",
                parse_mode='Markdown'
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик ошибок"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """Запуск бота"""
        application = Application.builder().token(self.token).build()
        
        # Регистрация обработчиков
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("about", self.about))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_url))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        application.add_error_handler(self.error_handler)
        
        # Запуск бота
        logger.info("Bot is starting...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
