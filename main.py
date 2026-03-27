import os
import asyncio
import yt_dlp
import random
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- 1. THE REPLIT "KEEP ALIVE" SERVER ---
# This creates a small webpage that we can "ping" to keep the bot awake.
app = Flask('')

@app.route('/')
def home():
    return "Durden is Online and Mining Audio Gold! 🎸"

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()

# --- 2. CONFIGURATION FROM SECRETS ---
TOKEN = os.environ.get('TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
# On Replit, we use the local folder instead of /sdcard/
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# --- 3. BOT LOGIC ---
USERS_FILE = 'users.txt'
SONGS_FILE = 'songs_log.txt'

def log_activity(user_id, song_title=None):
    if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w').close()
    with open(USERS_FILE, 'r') as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
    if song_title:
        with open(SONGS_FILE, 'a') as f:
            f.write(f"{song_title}\n")

LOADING_PHRASES = ["🎸 Tuning instruments...", "💎 Mining gold...", "🎧 Polishing MP3...", "⚡ Almost there!"]

def get_progress_bar(percentage):
    filled = int(10 * percentage / 100)
    return f"{'●' * filled}{'○' * (10 - filled)} {percentage}%"

async def progress_hook(d, update, context, status_msg):
    if d['status'] == 'downloading':
        try:
            p = float(d.get('_percent_str', '0%').replace('%',''))
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=status_msg.message_id,
                text=f"{random.choice(LOADING_PHRASES)}\n\n{get_progress_bar(p)}\n🚀 Speed: {d.get('_speed_str', 'N/A')}"
            )
        except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_activity(update.effective_user.id)
    await update.message.reply_text("⚡ **DURDEN DOWNLOADER** ⚡\nPaste a YouTube link below!")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    user_count = len(open(USERS_FILE).read().splitlines()) if os.path.exists(USERS_FILE) else 0
    await update.message.reply_text(f"📊 **Admin Stats**\nUsers: {user_count}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url: return
    
    status_msg = await update.message.reply_text("🎬 Initializing...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'progress_hooks': [lambda d: asyncio.get_event_loop().create_task(progress_hook(d, update, context, status_msg))],
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        
        log_activity(update.effective_user.id, info.get('title'))
        await update.message.reply_audio(audio=open(file_path, 'rb'), title=info.get('title'))
        await status_msg.delete()
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    keep_alive() # Starts the web server to trick Replit
    print("Durden is LIVE on Replit!")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
