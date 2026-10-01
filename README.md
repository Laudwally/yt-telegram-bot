# YouTube Telegram Bot

A Telegram bot: send it a YouTube link, it replies with the video (or audio-only, if the video
is too large). Built on [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot)
and [`yt-dlp`](https://github.com/yt-dlp/yt-dlp).

## Important things to know before running this

- **Telegram doesn't host your bot.** A bot is just a normal program that talks to Telegram's
  API — it needs to run somewhere continuously (this repo includes a setup for a Windows Server
  VM via Task Scheduler; see below).
- **Telegram's 50 MB file limit.** Bots can only send files up to 50 MB through the standard Bot
  API. This bot downloads video capped at 480p and checks the real file size afterward — if it's
  still too big, it tells the user to try "Audio only" instead, which is usually much smaller.
- **YouTube increasingly blocks automated downloads from datacenter/cloud IPs** (this includes
  Azure, AWS, GCP, etc. — not just this bot). `yt-dlp` is updated frequently to work around this,
  but there is no guarantee it will always succeed from a given server. If downloads start
  failing, `pip install --upgrade yt-dlp` first; if that doesn't help, the IP may be rate-limited
  or blocked outright.
- **Respect copyright.** Downloading and redistributing copyrighted video is against YouTube's
  Terms of Service in most cases. Use this for your own content, content you have permission to
  download, or material that's actually in the public domain / Creative Commons.

## Setup

### 1. Get a bot token

Message [@BotFather](https://t.me/BotFather) on Telegram, send `/newbot`, follow the prompts.
It gives you a token that looks like `123456789:AAH...`.

### 2. Install

Requires [ffmpeg](https://ffmpeg.org/) on `PATH` (needed to merge YouTube's separate video/audio
streams — modern YouTube almost never serves a single combined file).

```bash
python -m venv .venv
.venv\Scripts\activate          # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

copy .env.example .env          # cp .env.example .env on macOS/Linux
# then edit .env and paste your token
```

### 3. Run it

```bash
python bot.py
```

Message your bot on Telegram with a YouTube link — it'll ask whether you want the video or just
the audio.

## Deploying on a Windows Server VM (e.g. Azure)

This repo includes a Task Scheduler setup so the bot starts on boot and restarts automatically
if it crashes — no third-party service wrapper (like NSSM) required.

1. Clone this repo and complete the **Setup** steps above on the VM (including `.env` with your
   real token).
2. Open PowerShell **as Administrator** and run, from the project root:
   ```powershell
   powershell -ExecutionPolicy Bypass -File deploy\windows\install-task.ps1
   ```
3. Start it immediately (or just reboot):
   ```powershell
   Start-ScheduledTask -TaskName "YouTubeTelegramBot"
   ```
4. Logs land in `bot.log` in the project root. Check task status:
   ```powershell
   Get-ScheduledTask -TaskName "YouTubeTelegramBot" | Get-ScheduledTaskInfo
   ```

To remove it later: `deploy\windows\uninstall-task.ps1` (also as Administrator).

## Running the tests

```bash
pip install -r requirements.txt pytest
pytest tests/ -q
```

The test suite covers URL validation and config — it deliberately does **not** run a live
download against YouTube in CI, since cloud CI runners are exactly the kind of IP YouTube tends
to block (see caveats above), which would make the test suite flaky through no fault of the code.
The download logic was manually verified end-to-end (both the video and audio paths) against a
real YouTube video before this was committed.

## Project layout

```
downloader.py    YouTube download logic (yt-dlp), independent of Telegram
bot.py            Telegram handlers: /start, link detection, video/audio choice buttons
tests/             unit tests for the URL-matching and config logic
deploy/windows/     Task Scheduler setup scripts for a Windows Server VM
```
