import os
import asyncio
import yt_dlp
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIG ---
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
    # Check if the file actually exists on the Render server
    has_cookies = os.path.exists(COOKIE_FILE)
    status = "✅ Stealth Active (Cookies Loaded)" if has_cookies else "⚠️ Warning: cookies.txt not found!"
    await update.message.reply_text(f"⚡ **DURDEN V7** ⚡\n{status}\n\nSend any link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url: return 

    status_msg = await update.message.reply_text("🎬 Grabbing any available format...")

    ydl_opts = {
        # 'best' is the most compatible setting; it bypasses specific format errors
        'format': 'best', 
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128', # Lowering to 128kbps saves Render's RAM
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
            if not info:
                raise Exception("YouTube blocked the request. Refresh cookies.txt.")
            
            # Find the path of the downloaded/converted file
            base_filename = ydl.prepare_filename(info)
            file_path = os.path.splitext(base_filename)[0] + ".mp3"
        
        if os.path.exists(file_path):
            await update.message.reply_audio(audio=open(file_path, 'rb'), title=info.get('title'))
            os.remove(file_path)
        else:
            # Fallback if the MP3 extension logic fails
            await update.message.reply_text("❌ Download finished but file conversion failed.")
            
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
