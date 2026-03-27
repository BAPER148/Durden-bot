import os
import asyncio
import yt_dlp
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

TOKEN = os.environ.get('TOKEN')
DURDEN_FOLDER = 'downloads'
COOKIE_FILE = 'cookies.txt'

if not os.path.exists(DURDEN_FOLDER):
    os.makedirs(DURDEN_FOLDER)

# Specific Mobile User-Agent to match the headers
MOBILE_UA = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ Stealth Ready" if os.path.exists(COOKIE_FILE) else "⚠️ cookies.txt Missing"
    await update.message.reply_text(f"⚡ **DURDEN V8 (Mobile Identity)** ⚡\nStatus: {status}\n\nSend a link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url: return 

    status_msg = await update.message.reply_text("🎬 Mimicking Mobile Device...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'user_agent': MOBILE_UA,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        # This header makes YouTube think the request is coming from the official Android app
        'add_header': [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language: en-US,en;q=0.5',
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("YouTube still blocking. Please Refresh cookies.txt on GitHub.")
            
            file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        
        await context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=status_msg.message_id, text="✨ Sending...")
        with open(file_path, 'rb') as f:
            await update.message.reply_audio(audio=f, title=info.get('title'))
        
        if os.path.exists(file_path): os.remove(file_path)
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:150]}")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
