# summarizvid — Telegram Video Summarizer Bot

A Telegram bot that summarizes YouTube and TikTok videos using AI (Grok / OpenAI). Send a link — get a clean, readable summary of the video and its top comments.

## Features

- **YouTube & TikTok** — paste a link or use `/sum <url>`
- **Smart transcript extraction** — prefers native subtitles; falls back to Whisper transcription for videos without them
- **Video file support** — send an `.mp4` / `.mov` file directly to the bot
- **Comment analysis** — summarizes top comments alongside the video
- **Grok + OpenAI** — uses xAI Grok as primary model, OpenAI as automatic fallback
- **Access control** — optionally restrict to specific Telegram user IDs

## Quick Start

### Requirements

- Linux server with Python 3.10+
- `ffmpeg` (for audio extraction)
- Telegram bot token (from [@BotFather](https://t.me/BotFather))
- At least one AI API key: [xAI (Grok)](https://console.x.ai/) and/or [OpenAI](https://platform.openai.com/)

### Install

```bash
bash <(curl -s https://raw.githubusercontent.com/rustamnova/summarizvid/main/install.sh)
```

Or clone and run manually:

```bash
git clone https://github.com/rustamnova/summarizvid.git
cd summarizvid
bash install.sh
```

The installer will prompt you to paste your `.env`, install dependencies, and launch the bot in a `screen` session.

### Manual setup (without installer)

```bash
git clone https://github.com/rustamnova/summarizvid.git
cd summarizvid

cp .env.example .env
# Edit .env — fill in BOT_TOKEN and at least one AI key

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python summarizvid.py
```

## Configuration

Copy `.env.example` to `.env` and fill in your values:

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram bot token from @BotFather |
| `XAI_API_KEY` | one of two | xAI (Grok) API key — primary model |
| `XAI_MODEL` | — | Grok model (default: `grok-3-mini`) |
| `OPENAI_API_KEY` | one of two | OpenAI API key — fallback model |
| `OPENAI_MODEL` | — | OpenAI model (default: `gpt-4o-mini`) |
| `USER_IDS` | — | Comma-separated Telegram IDs allowed to use the bot. Leave empty to allow anyone. |
| `TRANSCRIPT_LANGS` | — | Preferred subtitle languages, e.g. `ru,en` (default: `ru,en`) |
| `SUMMARY_LANG` | — | Language of the output summary (default: `ru`) |
| `MAX_COMMENTS` | — | Max comments to analyze (default: `80`) |

## Usage

```
/sum https://www.youtube.com/watch?v=VIDEO_ID
/sum https://www.tiktok.com/@user/video/VIDEO_ID
```

You can also just send the URL as a plain message. For videos without subtitles, the bot will download audio and transcribe it via OpenAI Whisper — this takes 30–60 seconds depending on video length.

## Managing the bot

```bash
bash start.sh      # Start
bash stop.sh       # Stop
bash restart.sh    # Restart
screen -r summarizvid   # Attach to the running session
```

Logs are written to `logs/`:

| File | Contents |
|---|---|
| `logs/worklog.txt` | All activity (INFO+) |
| `logs/errors.txt` | Errors only (ERROR+) |
| `logs/install.txt` | Install log |

## Project structure

```
summarizvid.py    # Main bot
bot_logging.py    # Logging setup
install.sh        # One-command installer
start.sh          # Start script
stop.sh           # Stop script
restart.sh        # Restart script
requirements.txt  # Python dependencies
.env.example      # Config template
```

## License

MIT
