#!/usr/bin/env python3
import os
import re
import sys
import json
import uuid
import asyncio
import logging
import logging.handlers
import subprocess
import tempfile
from urllib.parse import urlparse, parse_qs

import httpx
import yt_dlp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from youtube_transcript_api import YouTubeTranscriptApi

# ---------------------------
# Config / ENV
# ---------------------------
load_dotenv(override=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
USER_IDS = set(int(x.strip()) for x in os.getenv("USER_IDS", "").split(",") if x.strip().isdigit())

XAI_API_KEY = os.getenv("XAI_API_KEY", "").strip() or os.getenv("GROK_API", "").strip()
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1").strip().rstrip("/")
XAI_MODEL = os.getenv("XAI_MODEL", "grok-4-latest").strip()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

SUMMARY_LANG = os.getenv("SUMMARY_LANG", "ru").strip()
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "900"))
TRANSCRIPT_LANGS = [x.strip() for x in os.getenv("TRANSCRIPT_LANGS", "ru,en").split(",") if x.strip()]
MAX_TRANSCRIPT_CHARS = int(os.getenv("MAX_TRANSCRIPT_CHARS", "120000"))
MAX_COMMENTS = int(os.getenv("MAX_COMMENTS", "80"))
MAX_COMMENT_CHARS = int(os.getenv("MAX_COMMENT_CHARS", "16000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing in .env")
if not XAI_API_KEY and not OPENAI_API_KEY:
    raise RuntimeError("Необходим хотя бы один ключ: XAI_API_KEY (или GROK_API) или OPENAI_API_KEY")

# ---------------------------
# Logging
# ---------------------------
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

_worklog_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "worklog.txt"), maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_worklog_handler.setLevel(logging.INFO)
_worklog_handler.setFormatter(_fmt)

_error_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "errors.txt"), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
)
_error_handler.setLevel(logging.ERROR)
_error_handler.setFormatter(_fmt)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_fmt)

logging.root.handlers.clear()
logging.root.setLevel(logging.INFO)
logging.root.addHandler(_worklog_handler)
logging.root.addHandler(_error_handler)
logging.root.addHandler(_console_handler)

log = logging.getLogger(__name__)


class SummaryError(Exception):
    pass


def allowed(user_id: int) -> bool:
    return not USER_IDS or user_id in USER_IDS


def detect_platform(url: str) -> str | None:
    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return None
    if "youtube.com" in host or "youtu.be" in host:
        return "youtube"
    if "tiktok.com" in host:
        return "tiktok"
    return None


def extract_youtube_video_id(url: str) -> str | None:
    try:
        parsed = urlparse(url.strip())
    except Exception:
        return None

    host = parsed.netloc.lower()
    path = parsed.path.strip("/")
    if "youtu.be" in host and path:
        return path.split("/")[0]
    if "youtube.com" in host:
        if path == "watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if path.startswith("shorts/") or path.startswith("embed/"):
            parts = path.split("/")
            if len(parts) >= 2:
                return parts[1]
    return None


def normalize_text(text: str) -> str:
    return " ".join((text or "").replace("\n", " ").split()).strip()


def parse_subtitle_payload(raw: str, ext: str) -> str:
    ext = (ext or "").lower()
    if ext == "json3":
        try:
            data = json.loads(raw)
            parts = []
            for evt in data.get("events", []):
                for seg in evt.get("segs", []):
                    t = normalize_text(seg.get("utf8", ""))
                    if t:
                        parts.append(t)
            return "\n".join(parts)
        except Exception:
            return ""

    text = raw.replace("\r", "")
    lines = []
    for line in text.split("\n"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("WEBVTT"):
            continue
        if s.startswith("NOTE"):
            continue
        if re.match(r"^\d+$", s):
            continue
        if "-->" in s:
            continue
        s = re.sub(r"<[^>]+>", "", s)
        s = normalize_text(s)
        if s:
            lines.append(s)
    return "\n".join(lines)


def fetch_text_from_subtitles(info: dict) -> str:
    langs = TRANSCRIPT_LANGS[:]
    for source in ("subtitles", "automatic_captions"):
        tracks_by_lang = info.get(source) or {}
        for lang in tracks_by_lang.keys():
            if lang not in langs:
                langs.append(lang)

        for lang in langs:
            tracks = tracks_by_lang.get(lang) or []
            if not tracks:
                continue
            preferred = sorted(
                tracks,
                key=lambda x: (0 if x.get("ext") in ("vtt", "json3", "srt", "ttml") else 1),
            )
            for track in preferred:
                url = track.get("url")
                ext = (track.get("ext") or "").lower()
                if not url:
                    continue
                try:
                    resp = httpx.get(url, timeout=30, follow_redirects=True)
                    resp.raise_for_status()
                    parsed = parse_subtitle_payload(resp.text, ext)
                    if parsed:
                        return parsed
                except Exception as e:
                    log.warning("subtitle.download.fail source=%s lang=%s ext=%s err=%s", source, lang, ext, e)
    return ""


def fetch_youtube_transcript(video_id: str) -> str:
    transcript = None
    if hasattr(YouTubeTranscriptApi, "get_transcript"):
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=TRANSCRIPT_LANGS)
    else:
        api = YouTubeTranscriptApi()
        if not hasattr(api, "fetch"):
            raise RuntimeError("Unsupported youtube-transcript-api version: missing get_transcript/fetch")
        fetched = api.fetch(video_id, languages=TRANSCRIPT_LANGS)
        if hasattr(fetched, "to_raw_data"):
            transcript = fetched.to_raw_data()
        else:
            transcript = []
            for item in fetched:
                if isinstance(item, dict):
                    transcript.append(item)
                else:
                    transcript.append({"text": getattr(item, "text", ""), "start": getattr(item, "start", 0.0)})

    lines = []
    total_chars = 0
    for item in transcript:
        text = normalize_text(item.get("text", ""))
        if not text:
            continue
        total_chars += len(text)
        if total_chars > MAX_TRANSCRIPT_CHARS:
            break
        lines.append(text)
    return "\n".join(lines).strip()


def fetch_media_info(url: str) -> dict:
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "getcomments": True,
        "socket_timeout": 20,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=False) or {}


def build_content_text(platform: str, url: str, info: dict) -> str:
    if platform == "youtube":
        video_id = extract_youtube_video_id(url)
        if video_id:
            try:
                text = fetch_youtube_transcript(video_id)
                if text:
                    return text
            except Exception as e:
                log.warning("youtube.transcript.api.fail err=%s", e)

    sub_text = fetch_text_from_subtitles(info)
    if sub_text:
        return sub_text[:MAX_TRANSCRIPT_CHARS]

    # Fallback: используем title/description если субтитров нет.
    title = normalize_text(info.get("title", ""))
    desc = normalize_text(info.get("description", ""))
    fallback = f"Title: {title}\nDescription: {desc}".strip()
    if fallback:
        return fallback[:MAX_TRANSCRIPT_CHARS]
    raise SummaryError("Не удалось получить текст видео (субтитры/описание недоступны)")


def extract_comments(info: dict) -> list[dict]:
    raw = info.get("comments") or []
    if not isinstance(raw, list):
        return []

    comments = []
    seen = set()
    total_chars = 0
    for c in raw:
        if not isinstance(c, dict):
            continue
        text = normalize_text(c.get("text", ""))
        if not text or text in seen:
            continue
        seen.add(text)
        like_count = c.get("like_count", 0)
        try:
            likes = int(like_count or 0)
        except Exception:
            likes = 0

        clipped = text[:500]
        total_chars += len(clipped)
        if total_chars > MAX_COMMENT_CHARS:
            break

        comments.append({"text": clipped, "likes": likes})
        if len(comments) >= MAX_COMMENTS:
            break
    return comments


def build_video_summary_prompt(platform: str, video_url: str, title: str, content_text: str) -> str:
    return (
        f"Сделай черновой конспект видео.\n"
        f"Платформа: {platform}\n"
        f"Язык ответа: {SUMMARY_LANG}\n"
        f"Ссылка: {video_url}\n"
        f"Заголовок: {title}\n\n"
        "Верни обычный текст в 3 секциях:\n"
        "1) Краткая суть (1 абзац)\n"
        "2) Основные идеи (5-8 пунктов)\n"
        "3) Практические выводы (3-5 пунктов)\n\n"
        "Требования:\n"
        "- Не выдумывай факты.\n"
        "- Не пиши таймкоды.\n"
        "- Если данных мало, укажи это явно.\n\n"
        f"Материал:\n{content_text}"
    )


_GROK_RETRYABLE_STATUSES = {429, 502, 503}


async def request_grok_summary(platform: str, video_url: str, title: str, content_text: str) -> str:
    if not XAI_API_KEY:
        raise SummaryError("XAI_API_KEY не задан")
    payload = {
        "model": XAI_MODEL,
        "temperature": 0.2,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [
            {"role": "system", "content": "Ты точный ассистент по суммаризации видео."},
            {"role": "user", "content": build_video_summary_prompt(platform, video_url, title, content_text)},
        ],
    }
    headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
    last_err: Exception | None = None
    for attempt in range(3):
        if attempt > 0:
            await asyncio.sleep(3 * attempt)
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                resp = await client.post(f"{XAI_BASE_URL}/chat/completions", headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            status = e.response.status_code if e.response is not None else 0
            body = e.response.text[:900] if e.response is not None else ""
            if status in _GROK_RETRYABLE_STATUSES and attempt < 2:
                log.warning("Grok API HTTP %s, retry %s/3 body=%s", status, attempt + 1, body[:200])
                last_err = e
                continue
            log.error("Grok API HTTP error: status=%s body=%s", status, body)
            raise SummaryError(f"Grok API вернул HTTP {status}") from e
        except httpx.HTTPError as e:
            log.error("Grok API network error: %s", e)
            raise SummaryError("Сетевой сбой при запросе к Grok API") from e
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
            log.error("Grok API parse error: %s", e)
            raise SummaryError("Некорректный ответ от Grok API") from e
        else:
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                log.error("Grok API empty content: %s", str(data)[:1000])
                raise SummaryError("Grok API вернул пустой ответ")
            return content.strip()

    raise SummaryError("Grok API временно недоступен после 3 попыток") from last_err


async def request_openai_summary(platform: str, video_url: str, title: str, content_text: str) -> str:
    if not OPENAI_API_KEY:
        raise SummaryError("OpenAI API недоступен — OPENAI_API_KEY не задан")
    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages": [
            {"role": "system", "content": "Ты точный ассистент по суммаризации видео."},
            {"role": "user", "content": build_video_summary_prompt(platform, video_url, title, content_text)},
        ],
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        body = e.response.text[:900] if e.response is not None else ""
        log.error("OpenAI summary HTTP error: status=%s body=%s", e.response.status_code if e.response else "n/a", body)
        raise SummaryError(f"OpenAI API вернул HTTP {e.response.status_code}") from e
    except httpx.HTTPError as e:
        log.error("OpenAI summary network error: %s", e)
        raise SummaryError("Сетевой сбой при запросе к OpenAI API") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        log.error("OpenAI summary parse error: %s", e)
        raise SummaryError("Некорректный ответ от OpenAI API") from e

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        log.error("OpenAI summary empty content: %s", str(data)[:1000])
        raise SummaryError("OpenAI API вернул пустой ответ")
    return content.strip()


async def request_summary_with_fallback(platform: str, video_url: str, title: str, content_text: str) -> str:
    """Пробует Grok, при ошибке — фоллбэк на OpenAI."""
    if XAI_API_KEY:
        try:
            return await request_grok_summary(platform, video_url, title, content_text)
        except SummaryError as e:
            if OPENAI_API_KEY:
                log.warning("Grok недоступен (%s), переключаюсь на OpenAI", e)
            else:
                raise
    return await request_openai_summary(platform, video_url, title, content_text)


async def request_openai_rewrite(video_url: str, platform: str, draft_summary: str) -> str:
    if not OPENAI_API_KEY:
        log.info("OPENAI_API_KEY не задан, пропускаю редактуру через ChatGPT")
        return f"{draft_summary.strip()}\n\nВидео: {video_url}"

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Ты редактор текста. Делай читабельный, грамотный, структурированный текст на русском языке."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Перепиши черновой суммариз в финальный формат.\n"
                    "Требования:\n"
                    "- Без таймкодов и служебных пометок.\n"
                    "- Сохрани факты и смысл.\n"
                    "- Структура: вводный абзац + ключевые мысли + практический вывод.\n"
                    f"- Платформа: {platform}\n"
                    f"- В конец добавь строку: Видео: {video_url}\n\n"
                    f"Черновой суммариз:\n{draft_summary}"
                ),
            },
        ],
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        body = e.response.text[:900] if e.response is not None else ""
        log.error("OpenAI API HTTP error: status=%s body=%s", e.response.status_code if e.response else "n/a", body)
        raise SummaryError(f"OpenAI API вернул HTTP {e.response.status_code}") from e
    except httpx.HTTPError as e:
        log.error("OpenAI API network error: %s", e)
        raise SummaryError("Сетевой сбой при запросе к OpenAI API") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        log.error("OpenAI API parse error: %s", e)
        raise SummaryError("Некорректный ответ от OpenAI API") from e

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        log.error("OpenAI API empty content: %s", str(data)[:1000])
        raise SummaryError("OpenAI API вернул пустой ответ")
    return content.strip()


async def request_openai_comments_summary(video_url: str, platform: str, comments: list[dict]) -> str:
    if not comments:
        return "Комментарии: не удалось получить комментарии для этого видео."

    top_popular = sorted(comments, key=lambda x: x.get("likes", 0), reverse=True)[:20]
    important_pool = comments[:20]
    serialized = []
    for idx, c in enumerate(important_pool, start=1):
        serialized.append(f"[C{idx}] likes={c.get('likes', 0)} text={c.get('text', '')}")
    popular_serialized = []
    for idx, c in enumerate(top_popular, start=1):
        popular_serialized.append(f"[P{idx}] likes={c.get('likes', 0)} text={c.get('text', '')}")

    if not OPENAI_API_KEY:
        main_idea = top_popular[0]["text"] if top_popular else comments[0]["text"]
        lines = [
            "Комментарии (best-effort):",
            f"Основная мысль: {main_idea}",
            "Популярные комментарии:",
        ]
        for c in top_popular[:5]:
            lines.append(f"- ({c.get('likes', 0)} likes) {c.get('text', '')}")
        return "\n".join(lines)

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": "Ты аналитик пользовательских комментариев. Пиши ясно и по делу на русском языке.",
            },
            {
                "role": "user",
                "content": (
                    f"Проанализируй комментарии к видео ({platform}) и верни читабельный текст.\n"
                    "Формат:\n"
                    "1) Основная мысль комментариев (1-2 предложения)\n"
                    "2) Важные комментарии (5 пунктов)\n"
                    "3) Популярные комментарии (5 пунктов, можно упоминать лайки)\n"
                    "4) Короткий вывод по настроению аудитории (1-2 предложения)\n\n"
                    f"Ссылка на видео: {video_url}\n\n"
                    "Выборка комментариев:\n"
                    + "\n".join(serialized)
                    + "\n\nПопулярные по лайкам:\n"
                    + "\n".join(popular_serialized)
                ),
            },
        ],
    }
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        body = e.response.text[:900] if e.response is not None else ""
        log.error("OpenAI comments HTTP error: status=%s body=%s", e.response.status_code if e.response else "n/a", body)
        raise SummaryError(f"OpenAI API (комментарии) вернул HTTP {e.response.status_code}") from e
    except httpx.HTTPError as e:
        log.error("OpenAI comments network error: %s", e)
        raise SummaryError("Сетевой сбой при анализе комментариев") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        log.error("OpenAI comments parse error: %s", e)
        raise SummaryError("Некорректный ответ OpenAI при анализе комментариев") from e

    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not content:
        raise SummaryError("OpenAI API вернул пустой анализ комментариев")
    return content.strip()


def extract_audio_ffmpeg(video_path: str, audio_path: str) -> None:
    """Extract audio from video file, compress to mono mp3 64kbps."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "mp3", "-ac", "1", "-ab", "64k", audio_path],
        capture_output=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise SummaryError(f"ffmpeg error: {result.stderr.decode()[:500]}")


async def transcribe_with_whisper(audio_path: str) -> str:
    """Transcribe audio file via OpenAI Whisper API. Returns plain text."""
    if not OPENAI_API_KEY:
        raise SummaryError("OPENAI_API_KEY не задан — транскрипция через Whisper недоступна")
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL}/audio/transcriptions",
            headers=headers,
            files={"file": (os.path.basename(audio_path), audio_bytes, "audio/mpeg")},
            data={"model": "whisper-1", "response_format": "text"},
        )
        resp.raise_for_status()
        return resp.text.strip()


async def summarize_video_file_and_reply(update: Update, file_id: str, file_name: str, file_size: int):
    trace_id = uuid.uuid4().hex[:8]
    user_id = update.effective_user.id

    MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024  # Telegram bot API limit
    if file_size > MAX_DOWNLOAD_BYTES:
        await update.message.reply_text(
            f"⚠️ Файл слишком большой ({file_size // 1024 // 1024} МБ).\n"
            "Telegram позволяет боту скачивать файлы до 20 МБ. Сожми видео или обрежь до нужного фрагмента."
        )
        return

    log.info("videofile.start trace=%s user=%s size=%s name=%s", trace_id, user_id, file_size, file_name)
    status_msg = await update.message.reply_text("⏳ Скачиваю видео...")

    tmpdir = tempfile.mkdtemp(prefix="summvid_")
    video_path = os.path.join(tmpdir, "video.mp4")
    audio_path = os.path.join(tmpdir, "audio.mp3")

    try:
        # 1. Download from Telegram
        file_obj = await update.effective_message.get_bot().get_file(file_id)
        await file_obj.download_to_drive(video_path)
        log.info("videofile.downloaded trace=%s bytes=%s", trace_id, os.path.getsize(video_path))

        # 2. Extract audio via ffmpeg
        await status_msg.edit_text("🔊 Извлекаю аудиодорожку...")
        await asyncio.to_thread(extract_audio_ffmpeg, video_path, audio_path)
        audio_size = os.path.getsize(audio_path)
        log.info("videofile.audio trace=%s audio_bytes=%s", trace_id, audio_size)

        if audio_size > 25 * 1024 * 1024:
            raise SummaryError("Аудиодорожка слишком длинная даже после сжатия (>25 МБ для Whisper). Обрежь видео.")

        # 3. Transcribe via Whisper
        await status_msg.edit_text("🎙 Распознаю речь (Whisper)...")
        transcript = await transcribe_with_whisper(audio_path)
        if not transcript:
            raise SummaryError("Whisper не распознал речь — возможно, видео без голоса или слишком тихое")
        log.info("videofile.transcript trace=%s chars=%s preview=%s", trace_id, len(transcript), transcript[:80])

        # 4. Summarize via Grok (or OpenAI fallback)
        await status_msg.edit_text("🤖 Анализирую содержимое...")
        title = file_name or "Видеофайл"
        raw_summary = await request_summary_with_fallback("file", title, title, transcript[:MAX_TRANSCRIPT_CHARS])
        log.info("videofile.summary.ok trace=%s", trace_id)

        # 5. Rewrite via OpenAI
        final_summary = await request_openai_rewrite(title, "file", raw_summary)
        log.info("videofile.openai.ok trace=%s", trace_id)

        await status_msg.delete()

    except SummaryError as e:
        log.error("videofile.fail trace=%s reason=%s", trace_id, e)
        await status_msg.edit_text(f"❌ {e}\nКод: {trace_id}")
        return
    except Exception:
        log.exception("videofile.fail trace=%s unexpected", trace_id)
        await status_msg.edit_text(f"❌ Неожиданная ошибка при обработке файла. Код: {trace_id}")
        return
    finally:
        for p in (video_path, audio_path):
            try:
                os.unlink(p)
            except Exception:
                pass
        try:
            os.rmdir(tmpdir)
        except Exception:
            pass

    chunk_size = 3900
    for i in range(0, len(final_summary), chunk_size):
        await update.message.reply_text(final_summary[i : i + chunk_size])
    log.info("videofile.done trace=%s chunks=%s", trace_id, (len(final_summary) + chunk_size - 1) // chunk_size)


def get_url_from_text(text: str) -> str | None:
    match = re.search(r"(https?://\S+)", text or "")
    return match.group(1).strip() if match else None


async def summarize_video_and_reply(update: Update, url: str):
    trace_id = uuid.uuid4().hex[:8]
    platform = detect_platform(url)
    if platform not in ("youtube", "tiktok"):
        await update.message.reply_text("Поддерживаются только YouTube и TikTok ссылки.")
        return

    log.info("sum.start trace=%s user=%s platform=%s model=%s", trace_id, update.effective_user.id, platform, XAI_MODEL)
    await update.message.reply_text("Анализирую видео и комментарии. Это может занять 1-2 минуты.")

    try:
        log.info("sum.meta.fetch trace=%s", trace_id)
        info = await asyncio.to_thread(fetch_media_info, url)
        title = normalize_text(info.get("title", "")) or "Без названия"
        log.info("sum.meta.ok trace=%s title=%s", trace_id, title[:120])

        log.info("sum.content.fetch trace=%s", trace_id)
        content_text = await asyncio.to_thread(build_content_text, platform, url, info)
        log.info("sum.content.ok trace=%s chars=%s", trace_id, len(content_text))

        log.info("sum.summary.request trace=%s", trace_id)
        raw_summary = await request_summary_with_fallback(platform, url, title, content_text)
        log.info("sum.summary.ok trace=%s chars=%s", trace_id, len(raw_summary))

        log.info("sum.openai.video.request trace=%s model=%s", trace_id, OPENAI_MODEL)
        final_video_summary = await request_openai_rewrite(url, platform, raw_summary)
        log.info("sum.openai.video.ok trace=%s chars=%s", trace_id, len(final_video_summary))

        comments = await asyncio.to_thread(extract_comments, info)
        log.info("sum.comments.extract trace=%s count=%s", trace_id, len(comments))

        try:
            log.info("sum.openai.comments.request trace=%s", trace_id)
            comments_block = await request_openai_comments_summary(url, platform, comments)
            log.info("sum.openai.comments.ok trace=%s chars=%s", trace_id, len(comments_block))
        except SummaryError as e:
            log.error("sum.openai.comments.fail trace=%s reason=%s", trace_id, e)
            comments_block = "Комментарии: не удалось обработать комментарии для этого видео."

        result = f"{final_video_summary}\n\nКомментарии:\n{comments_block}"
    except SummaryError as e:
        log.error("sum.fail trace=%s reason=%s", trace_id, e)
        await update.message.reply_text(f"Ошибка обработки: {e}. Код: {trace_id}")
        return
    except Exception:
        log.exception("sum.fail trace=%s unexpected", trace_id)
        await update.message.reply_text(f"Ошибка при обработке видео. Код: {trace_id}")
        return

    chunk_size = 3900
    for i in range(0, len(result), chunk_size):
        await update.message.reply_text(result[i : i + chunk_size])
    log.info("sum.done trace=%s chunks=%s", trace_id, (len(result) + chunk_size - 1) // chunk_size)


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    log.info("/start от %s", update.effective_user.id)
    await update.message.reply_text(
        "Привет! Я суммаризатор видео.\n\n"
        "Что умею:\n"
        "• YouTube / TikTok ссылка — суммариз + анализ комментариев\n"
        "• Видеофайл (до 20 МБ) — транскрипция через Whisper + суммариз\n\n"
        "Команды:\n"
        "/sum <url> — суммаризировать видео по ссылке\n\n"
        "Или просто пришли ссылку / видеофайл 🎥"
    )


async def cmd_ping(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    await update.message.reply_text("Pong!")


async def cmd_sum(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    url = ctx.args[0] if ctx.args else None
    if not url:
        await update.message.reply_text("Использование: /sum <youtube_or_tiktok_url>")
        return
    await summarize_video_and_reply(update, url)


async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    url = get_url_from_text(update.message.text or "")
    if not url:
        return
    if detect_platform(url) not in ("youtube", "tiktok"):
        return
    await summarize_video_and_reply(update, url)


async def on_video_file(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        return
    msg = update.message
    if msg.video:
        file_id = msg.video.file_id
        file_size = msg.video.file_size or 0
        file_name = getattr(msg.video, "file_name", None) or "video.mp4"
    elif msg.document and (msg.document.mime_type or "").startswith("video/"):
        file_id = msg.document.file_id
        file_size = msg.document.file_size or 0
        file_name = msg.document.file_name or "video.mp4"
    else:
        return
    await summarize_video_file_and_reply(update, file_id, file_name, file_size)


def main():
    log.info("=== Запуск бота ===")
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("ping", cmd_ping))
    app.add_handler(CommandHandler("sum", cmd_sum))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), on_text))
    app.add_handler(MessageHandler(filters.VIDEO, on_video_file))
    app.add_handler(MessageHandler(filters.Document.VIDEO, on_video_file))
    log.info("Бот запущен, ожидание обновлений...")
    app.run_polling(drop_pending_updates=True)
    log.info("=== Остановка бота ===")


if __name__ == "__main__":
    main()
