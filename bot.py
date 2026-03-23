import socket
import requests
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8628570427:AAEKsZVwJ00QxWYk6PBy1LobFmxZUiaW8y0"  # переменная окружения

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправь /check сайт (например: /check google.com)")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Напиши сайт: /check example.com")
        return
    site = context.args[0]
    try:
        ip = socket.gethostbyname(site)
    except:
        await update.message.reply_text("Ошибка: не удалось получить IP")
        return
    try:
        r = requests.get("http://" + site, timeout=5)
        status = r.status_code
    except:
        status = "не отвечает"
    result = f"Сайт: {site}\nIP: {ip}\nСтатус: {status}"
    await update.message.reply_text(result)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("check", check))
app.run_polling()