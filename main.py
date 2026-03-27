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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ Stealth Active" if os.path.exists(COOKIE_FILE) else "⚠️ No cookies.txt"
    await update.message.reply_text(f"⚡ **DURDEN V7 (Low RAM Mode)** ⚡\nStatus: {status}\n\nSend any YouTube link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url: return 

    status_msg = await update.message.reply_text("🎬 Fetching... (Low-res mode for stability)")

    ydl_opts = {
        # 'best' instead of 'bestaudio' finds a format 100% of the time
        'format': 'best', 
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', # 128kbps is easier on Render's memory
        }],
        'quiet': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'user_agent': random.choice(USER_AGENTS),
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info: raise Exception("Format block. Refresh cookies.")
            file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        
        await context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=status_msg.message_id, text="✨ Sending audio...")
        with open(file_path, 'rb') as f:
            await update.message.reply_audio(audio=f, title=info.get('title'))
        
        if os.path.exists(file_path): os.remove(file_path)
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
                              
