import os
import asyncio
import yt_dlp
import json
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIG ---
TOKEN = os.environ.get('TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0)) # Add your ID in Render Env Vars
DURDEN_FOLDER = 'downloads'
COOKIE_FILE = 'cookies.txt'
STATS_FILE = 'stats.json'

if not os.path.exists(DURDEN_FOLDER):
    os.makedirs(DURDEN_FOLDER)

# --- STATS LOGIC ---
def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            return json.load(f)
    return {"total": 0, "users": []}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = "✅ Stealth Active" if os.path.exists(COOKIE_FILE) else "⚠️ No cookies.txt"
    await update.message.reply_text(f"⚡ **DURDEN V11** ⚡\nStatus: {status}\n\nSend a link!")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_stats()
    await update.message.reply_text(f"📊 **Stats**\nUsers: {len(data['users'])}\nDownloads: {data['total']}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url: return 

    status_msg = await update.message.reply_text("🎬 Bypassing...")

    # Aggressive Stealth & Format Fix
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '128'}],
        'quiet': True,
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None,
        'user_agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        'nocheckcertificate': True,
        'ignoreerrors': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
        
        await update.message.reply_audio(audio=open(file_path, 'rb'), title=info.get('title'))
        
        # Update Stats
        stats = load_stats()
        stats["total"] += 1
        if update.effective_user.id not in stats["users"]:
            stats["users"].append(update.effective_user.id)
        save_stats(stats)

        os.remove(file_path)
        await status_msg.delete()
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:150]}")

def main():
    if not TOKEN: return
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
    
