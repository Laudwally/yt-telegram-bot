"""Telegram bot: send it a YouTube link, it replies with the video (or audio).

Run with: python bot.py
Requires TELEGRAM_BOT_TOKEN to be set (env var, or in a .env file — see README).
"""

from __future__ import annotations

import logging
import os
import shutil

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from downloader import DownloadError, download_audio, download_video, get_video_info, is_youtube_url, make_temp_download_dir

load_dotenv()

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
logger = logging.getLogger("yt-telegram-bot")


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a YouTube link and I'll download it for you "
        "(video if it fits Telegram's 50 MB limit, audio-only otherwise)."
    )


async def handle_message(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    if not is_youtube_url(text):
        await update.message.reply_text("That doesn't look like a YouTube link. Send me a youtube.com or youtu.be URL.")
        return

    try:
        info = get_video_info(text)
    except Exception:
        logger.exception("Failed to fetch video info for %s", text)
        await update.message.reply_text(
            "Couldn't read that video's info. It may be private, age-restricted, or YouTube is "
            "blocking this server's requests right now."
        )
        return

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🎬 Video", callback_data=f"video|{text}"),
                InlineKeyboardButton("🎵 Audio only", callback_data=f"audio|{text}"),
            ]
        ]
    )
    minutes, seconds = divmod(info.duration_seconds, 60)
    await update.message.reply_text(
        f"*{info.title}*\nby {info.uploader} · {minutes}:{seconds:02d}\n\nWhat would you like?",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def handle_choice(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    kind, url = query.data.split("|", 1)

    await query.edit_message_text(f"Downloading {kind}… this can take a minute.")

    temp_dir = make_temp_download_dir()
    try:
        if kind == "video":
            path = download_video(url, temp_dir)
            with open(path, "rb") as f:
                await query.message.reply_video(f, caption="Here you go 🎬", read_timeout=120, write_timeout=120)
        else:
            path = download_audio(url, temp_dir)
            with open(path, "rb") as f:
                await query.message.reply_audio(f, caption="Here you go 🎵", read_timeout=120, write_timeout=120)
        await query.edit_message_text("Done ✅")
    except DownloadError as e:
        logger.warning("Download failed for %s: %s", url, e)
        await query.edit_message_text(f"Couldn't fetch that one: {e}")
    except Exception:
        logger.exception("Unexpected error downloading %s", url)
        await query.edit_message_text("Something went wrong on my end. Please try again.")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def build_app() -> Application:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not set. Create a .env file (see .env.example) or set the "
            "environment variable before running the bot."
        )

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_choice))
    return app


def main() -> None:
    app = build_app()
    logger.info("Bot starting (long polling)...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
