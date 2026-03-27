import os
import asyncio
import yt_dlp
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = os.environ.get('TOKEN')
DURDEN_FOLDER = 'downloads'
COOKIE_FILE = 'cookies.txt'

# Ensure the download folder exists for Render
if not os.path.exists(DURDEN_FOLDER):
    os.makedirs(DURDEN_FOLDER)

# 10 Diverse User-Agents to mimic different real users
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0"
]

async def progress_hook(d, update, context, status_msg):
    if d['status'] == 'downloading':
        try:
            p = d.get('_percent_str', '0%').strip()
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=status_msg.message_id,
                text=f"🎧 **Durden is working...**\n\nProgress: {p}\n🚀 Speed: {d.get('_speed_str', 'N/A')}"
            )
        except:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚡ **DURDEN V4 (Ultra Stealth)** ⚡\n\nI am now using your cookies and rotating identities to bypass blocks. Send a YouTube link!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        return 

    status_msg = await update.message.reply_text("🎬 Initializing bypass...")

        ydl_opts = {
        # This tells yt-dlp to try the best audio, or fallback to the next best thing
        'format': 'bestaudio/best', 
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'progress_hooks': [lambda d: asyncio.get_event_loop().create_task(progress_hook(d, update, context, status_msg))],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'user_agent': random.choice(USER_AGENTS),
        'referer': 'https://www.google.com/',
        # ADD THESE TWO LINES TO FIX YOUR ERROR:
        'ignoreerrors': True,
        'noplaylist': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        
        await context.bot.edit_message_text(chat_id=update.message.chat_id, message_id=status_msg.message_id, text="✨ Success! Sending audio...")
        with open(file_path, 'rb') as f:
            await update.message.reply_audio(audio=f, title=info.get('title'))
        
        if os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()

    except Exception as e:
        error_text = str(e)
        if "Sign in to confirm" in error_text:
            await update.message.reply_text("❌ Cookie Error: YouTube rejected the session. Please refresh your `cookies.txt` file.")
        else:
            await update.message.reply_text(f"❌ Error: {error_text[:100]}...")

def main():
    if not TOKEN:
        print("Set your TOKEN in environment variables!")
        return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Durden Bot is Live.")
    app.run_polling()

if __name__ == '__main__':
    main()
  
