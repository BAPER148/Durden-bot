import os
import asyncio
import yt_dlp
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes

# --- CONFIGURATION ---
TOKEN = '8713046713:AAGU7NDi1ru8lhpVobxD5oFLtAoEU4rgL10'
DURDEN_FOLDER = '/sdcard/Durden'
ADMIN_ID = 6236244844  # <--- REPLACE THIS with your real Telegram ID (from @userinfobot)

# Files for tracking
USERS_FILE = 'users.txt'
SONGS_FILE = 'songs_log.txt'

if not os.path.exists(DURDEN_FOLDER):
    os.makedirs(DURDEN_FOLDER)

# --- STATS LOGGING LOGIC ---
def log_activity(user_id, song_title=None):
    # Log Unique User
    if not os.path.exists(USERS_FILE): open(USERS_FILE, 'w').close()
    with open(USERS_FILE, 'r') as f:
        users = f.read().splitlines()
    if str(user_id) not in users:
        with open(USERS_FILE, 'a') as f:
            f.write(f"{user_id}\n")
    
    # Log Song Title (if provided)
    if song_title:
        with open(SONGS_FILE, 'a') as f:
            f.write(f"{song_title}\n")

# --- UI HELPERS ---
LOADING_PHRASES = [
    "ðŸŽ¸ Tuning the instruments...",
    "ðŸ›°ï¸ Connecting to the satellite...",
    "ðŸ’Ž Mining for audio gold...",
    "ðŸŽ§ Polishing the MP3...",
    "ðŸ”¥ Durden is working hard...",
    "âš¡ Almost there, hang tight!"
]

def get_progress_bar(percentage):
    length = 10
    filled = int(length * percentage / 100)
    bar = 'â—' * filled + 'â—‹' * (length - filled)
    return f"{bar} {percentage}%"

async def progress_hook(d, update, context, status_msg):
    if d['status'] == 'downloading':
        p = d.get('_percent_str', '0%').replace('%','').strip()
        try:
            p_float = float(p)
            bar = get_progress_bar(p_float)
            phrase = random.choice(LOADING_PHRASES)
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=status_msg.message_id,
                text=f"{phrase}\n\n{bar}\nðŸš€ Speed: {d.get('_speed_str', 'N/A')}"
            )
        except:
            pass

# --- COMMAND HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_activity(update.effective_user.id)
    await update.message.reply_text(
        "âš¡ **Welcome to Durden Downloader** âš¡\n\n"
        "Send me a YouTube link and I'll handle the rest.\n"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-only command to see bot performance"""
    if update.effective_user.id != ADMIN_ID:
        return # Ignore if not admin

    # Count Users
    user_count = 0
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            user_count = len(f.read().splitlines())
    
    # Count Total Downloads
    song_count = 0
    last_song = "None yet"
    if os.path.exists(SONGS_FILE):
        with open(SONGS_FILE, 'r') as f:
            songs = f.read().splitlines()
            song_count = len(songs)
            if songs: last_song = songs[-1]

    stats_text = (
        "ðŸ“Š **DURDEN ADMIN PANEL**\n\n"
        f"ðŸ‘¤ **Unique Users:** {user_count}\n"
        f"ðŸŽµ **Total Downloads:** {song_count}\n"
        f"ðŸŽ§ **Last Track:** `{last_song}`"
    )
    await update.message.reply_text(stats_text, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" not in url and "youtu.be" not in url:
        return 

    status_msg = await update.message.reply_text("ðŸŽ¬ Initializing...")

    def my_hook(d):
        loop = asyncio.get_event_loop()
        loop.create_task(progress_hook(d, update, context, status_msg))

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DURDEN_FOLDER}/%(title)s.%(ext)s',
        'progress_hooks': [my_hook],
        'writethumbnail': True,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            temp_name = ydl.prepare_filename(info)
            final_name = os.path.splitext(temp_name)[0] + ".mp3"
            song_title = info.get('title', 'Unknown Title')
        
        # Log this specific download
        log_activity(update.effective_user.id, song_title)

        await context.bot.edit_message_text(
            chat_id=update.message.chat_id,
            message_id=status_msg.message_id,
            text="âœ¨ Done! Sending to your chat now..."
        )

        with open(final_name, 'rb') as audio_file:
            await update.message.reply_audio(
                audio=audio_file,
                title=os.path.basename(final_name),
                caption="Enjoy your music! ðŸŽµ"
            )
        
        await status_msg.delete()

        if os.path.exists(final_name):
            os.remove(final_name)
        
    except Exception as e:
        await update.message.reply_text(f"âŒ Error: {str(e)}")
        if 'final_name' in locals() and os.path.exists(final_name):
            os.remove(final_name)

def main():
    print("Durden Bot is running...")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats)) # New Stats Command
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
        
