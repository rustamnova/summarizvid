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
import base64
import glob
import shutil
import tempfile
from urllib.parse import urlparse, parse_qs

from bot_logging import setup_bot_logging

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
# Grok выключен по умолчанию: аккаунт исчерпал кредиты и отдаёт 403 на каждый
# запрос, из-за чего каждое видео впустую ждало таймаут перед фоллбэком.
# Вернуть в строй: USE_GROK=1 в .env после пополнения баланса xAI.
USE_GROK = os.getenv("USE_GROK", "0").strip().lower() in {"1", "true", "yes"}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip().rstrip("/")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

# Модели под конкретные задачи: дешёвая OPENAI_MODEL осталась только на
# второстепенных вещах (разбор комментариев), а тяжёлую работу — распознавание
# текста на кадрах и финальный пересказ — делают сильные модели.
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-5.5").strip()
VISION_MODEL = os.getenv("VISION_MODEL", "gpt-5.4").strip()
# Diarize размечает реплики по говорящим — это то, что превращает «поток слов»
# в читаемый диалог. При сбое откатываемся на обычные модели транскрипции.
TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize").strip()
TRANSCRIBE_FALLBACKS = ["gpt-4o-transcribe", "whisper-1"]

# MTProto (Telethon) — для скачивания файлов больше 20 МБ (лимит Bot API).
# Через MTProto бот тем же токеном может качать до 2 ГБ.
TELETHON_API_ID = int(os.getenv("TELETHON_API_ID", "0"))
TELETHON_API_HASH = os.getenv("TELETHON_API_HASH", "").strip()
MTPROTO_SESSION = os.path.join(BASE_DIR, "summarizvid_mtproto")
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "2000"))  # жёсткий потолок Telegram — 2 ГБ

SUMMARY_LANG = os.getenv("SUMMARY_LANG", "ru").strip()
# Финальный пересказ намеренно длиннее прежних 900 токенов (MAX_OUTPUT_TOKENS):
# в старый лимит подробный разговор не помещался и модель выбрасывала как раз
# содержание реплик.
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "6000"))

# Кадры для распознавания текста и описания картинки.
VISION_MAX_FRAMES = int(os.getenv("VISION_MAX_FRAMES", "32"))
VISION_FRAME_EVERY_SEC = float(os.getenv("VISION_FRAME_EVERY_SEC", "4"))
# detail=high обязателен: при low кадр ужимается до 512x512 и мелкие титры,
# субтитры и надписи становятся физически нечитаемыми.
VISION_DETAIL = os.getenv("VISION_DETAIL", "high").strip()

# Лимит /audio/transcriptions — 25 МБ на файл, поэтому длинное аудио режем на
# куски по времени и склеиваем результат.
AUDIO_CHUNK_SEC = int(os.getenv("AUDIO_CHUNK_SEC", "900"))
WHISPER_SIZE_LIMIT = 24 * 1024 * 1024
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
log = setup_bot_logging(__name__, __file__)


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


def _uses_completion_tokens(model: str) -> bool:
    """True для моделей, которые не принимают max_tokens (семейства gpt-5 и o-*)."""
    m = model.lower()
    return m.startswith("gpt-5") or m.startswith("o1") or m.startswith("o3") or m.startswith("o4")


async def openai_chat(
    messages: list,
    model: str,
    max_tokens: int,
    temperature: float | None = 0.2,
    timeout: float = 180,
    what: str = "OpenAI",
) -> str:
    """Единая точка вызова OpenAI chat/completions с разбором ошибок.

    Сам подставляет max_completion_tokens вместо max_tokens там, где этого
    требует модель (gpt-5.x / o-серия отвергают max_tokens с HTTP 400).
    """
    if not OPENAI_API_KEY:
        raise SummaryError("OPENAI_API_KEY не задан")

    payload: dict = {"model": model, "messages": messages}
    if _uses_completion_tokens(model):
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature

    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            # Часть моделей (например gpt-5.5) принимает только temperature=1 и
            # отвечает 400. Поддержка отличается даже внутри одного семейства,
            # поэтому не угадываем по имени, а повторяем запрос без параметра.
            if resp.status_code == 400 and "temperature" in resp.text and "temperature" in payload:
                log.info("%s: модель %s не принимает temperature, повторяю без неё", what, model)
                payload.pop("temperature")
                resp = await client.post(f"{OPENAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else 0
        body = e.response.text[:900] if e.response is not None else ""
        log.error("%s HTTP error: status=%s body=%s", what, status, body)
        raise SummaryError(f"{what}: API вернул HTTP {status}") from e
    except httpx.HTTPError as e:
        log.error("%s network error: %s", what, e)
        raise SummaryError(f"{what}: сетевой сбой") from e
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as e:
        log.error("%s parse error: %s", what, e)
        raise SummaryError(f"{what}: некорректный ответ API") from e

    content = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "")
    if not content:
        log.error("%s empty content: %s", what, str(data)[:1000])
        raise SummaryError(f"{what}: API вернул пустой ответ")
    return content.strip()


_GROK_RETRYABLE_STATUSES = {429, 502, 503}


async def request_grok_chat(system_prompt: str, user_prompt: str, max_tokens: int) -> str:
    """Запрос к Grok с готовыми промптами. Живёт только при USE_GROK=1."""
    if not XAI_API_KEY:
        raise SummaryError("XAI_API_KEY не задан")
    payload = {
        "model": XAI_MODEL,
        "temperature": 0.2,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
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


def build_multimodal_prompt(title: str, speech: str, screen_text: str, visual: str) -> str:
    """Промпт финального пересказа видеофайла.

    Главное отличие от старого build_video_summary_prompt: жёсткая рамка
    «суть / идеи / практические выводы» убрана. На разговорном видео она
    заставляла модель выжимать несуществующие «выводы» и выбрасывать сам
    разговор. Теперь речь — приоритет, а картинка и текст с экрана идут
    отдельными блоками и только как дополнение.
    """
    blocks = [f"НАЗВАНИЕ: {title}"]
    if speech:
        blocks.append(
            "РАСШИФРОВКА РЕЧИ (может содержать разметку по говорящим и таймкоды):\n" + speech
        )
    else:
        blocks.append("РАСШИФРОВКА РЕЧИ: речь не распознана или её нет.")
    if screen_text:
        blocks.append("ТЕКСТ, РАСПОЗНАННЫЙ НА ЭКРАНЕ:\n" + screen_text)
    if visual:
        blocks.append("ОПИСАНИЕ ВИДЕОРЯДА:\n" + visual)

    return (
        "Ты пересказываешь содержание видео человеку, который его не смотрел.\n"
        f"Язык ответа: {SUMMARY_LANG}.\n\n"
        "ГЛАВНОЕ: если в видео говорят — основа ответа это то, О ЧЁМ говорят. "
        "Передай содержание разговора подробно: какие темы поднимают, какие "
        "аргументы и факты звучат, к чему приходят. Если это диалог или интервью — "
        "покажи, кто какую позицию занимает и как развивается разговор. "
        "Приводи show-stopper реплики дословно в кавычках там, где формулировка важна. "
        "Не сжимай разговор до пары общих фраз — потерять содержание речи хуже, "
        "чем написать длиннее.\n\n"
        "Структура ответа:\n"
        "1. «О чём видео» — 2-3 предложения по сути.\n"
        "2. «Содержание» — подробный пересказ того, что говорят и что происходит, "
        "по ходу видео. Основной и самый объёмный блок. Разбей на абзацы или пункты.\n"
        "3. «Текст на экране» — если распознан: перечисли, что написано. "
        "Блок целиком опусти, если текста нет.\n"
        "4. «Что показано» — 2-4 предложения про картинку: место, люди, формат. "
        "Опусти, если видеоряд ничего не добавляет.\n"
        "5. «Итог» — 1-2 предложения.\n\n"
        "Правила:\n"
        "- Не выдумывай факты и имена, которых нет в материалах.\n"
        "- Если речь не распознана, честно скажи это в начале и опиши видео "
        "по тексту с экрана и картинке.\n"
        "- Метки «Говорящий A/B» заменяй на роли или имена, если они понятны "
        "из контекста; иначе пиши «первый собеседник», «второй собеседник».\n"
        "- Без служебных пометок и markdown-заголовков с решётками, "
        "названия блоков пиши обычным текстом.\n\n"
        "МАТЕРИАЛЫ:\n\n" + "\n\n".join(blocks)
    )


async def summarize_multimodal(
    title: str, speech: str, screen_text: str = "", visual: str = "", video_url: str = ""
) -> str:
    """Финальный пересказ видео одним проходом сильной модели.

    Раньше здесь стояла цепочка «черновой конспект → переписать черновик»:
    второй проход пересказывал уже сжатый текст и стабильно терял реплики.
    """
    system_prompt = (
        "Ты внимательный ассистент, который подробно и точно "
        "пересказывает содержание видео на русском языке."
    )
    user_prompt = build_multimodal_prompt(title, speech, screen_text, visual)

    text = ""
    if USE_GROK and XAI_API_KEY:
        try:
            text = await request_grok_chat(system_prompt, user_prompt, SUMMARY_MAX_TOKENS)
        except SummaryError as e:
            if not OPENAI_API_KEY:
                raise
            log.warning("Grok недоступен (%s), переключаюсь на OpenAI", e)

    if not text:
        text = await openai_chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=SUMMARY_MODEL,
            max_tokens=SUMMARY_MAX_TOKENS,
            timeout=300,
            what="OpenAI (пересказ)",
        )
    if video_url:
        text = f"{text}\n\nВидео: {video_url}"
    return text


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

    return await openai_chat(
        [
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
        model=OPENAI_MODEL,
        max_tokens=1500,
        timeout=90,
        what="OpenAI (комментарии)",
    )


def has_audio_stream(video_path: str) -> bool:
    """Return True if video has at least one audio stream."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type", "-of", "csv=p=0", video_path],
        capture_output=True, timeout=30,
    )
    return bool(probe.stdout.strip())


def extract_audio_ffmpeg(video_path: str, audio_path: str) -> None:
    """Extract audio from video file, compress to mono mp3 64kbps."""
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "mp3", "-ac", "1", "-ab", "64k", audio_path],
        capture_output=True,
        timeout=180,
    )
    if result.returncode != 0:
        err = result.stderr.decode(errors="replace")
        raise SummaryError(f"ffmpeg error: {err[-400:]}")


def probe_duration(path: str) -> float:
    """Длительность медиафайла в секундах (0.0, если ffprobe не смог)."""
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path],
        capture_output=True, timeout=30,
    )
    try:
        return float(probe.stdout.strip())
    except ValueError:
        return 0.0


def extract_frames_ffmpeg(video_path: str, frames_dir: str) -> list:
    """Нарезает кадры примерно раз в VISION_FRAME_EVERY_SEC секунд.

    Раньше бралось ровно 6 кадров на любое видео, поэтому у длинного ролика
    между соседними кадрами выпадали минуты — вместе с надписями на экране.
    Число кадров теперь зависит от длительности и упирается в VISION_MAX_FRAMES.
    Качество JPEG высокое (-q:v 2): кадр уходит в OCR, артефакты сжатия мешают
    читать мелкий текст.
    """
    duration = probe_duration(video_path) or 10.0
    n_frames = int(min(VISION_MAX_FRAMES, max(4, duration // VISION_FRAME_EVERY_SEC)))
    interval = max(duration / n_frames, 0.3)
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_path, "-vf", f"fps=1/{interval:.2f}",
         "-vframes", str(n_frames), "-q:v", "2",
         os.path.join(frames_dir, "frame_%03d.jpg")],
        capture_output=True, timeout=300,
    )
    return sorted(glob.glob(os.path.join(frames_dir, "frame_*.jpg")))


def _frames_as_content(frame_paths: list, instruction: str, duration: float) -> list:
    """Собирает content-массив для vision-запроса: инструкция + кадры с таймкодами."""
    content: list = [{"type": "text", "text": instruction}]
    step = (duration / len(frame_paths)) if (duration and frame_paths) else 0
    for idx, path in enumerate(frame_paths):
        if step:
            ts = int(idx * step)
            content.append({"type": "text", "text": f"[кадр {idx + 1}, ~{ts // 60:02d}:{ts % 60:02d}]"})
        else:
            content.append({"type": "text", "text": f"[кадр {idx + 1}]"})
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": VISION_DETAIL},
        })
    return content


async def ocr_frames(frame_paths: list, duration: float = 0.0) -> str:
    """Распознаёт весь текст, видимый на кадрах.

    Отдельный проход, а не пункт в общем описании: когда OCR был одним из
    требований в длинной инструкции «опиши что происходит», модель почти всегда
    ограничивалась пересказом картинки и текст игнорировала.
    """
    instruction = (
        "Ты OCR-движок. Перед тобой кадры из видео по порядку.\n"
        "Выпиши ДОСЛОВНО весь текст, который видно на кадрах: заголовки, титры, "
        "субтитры, подписи, надписи на объектах, имена и должности спикеров, "
        "названия, цифры, даты, ссылки, водяные знаки, текст в интерфейсе.\n\n"
        "Правила:\n"
        "- Сохраняй оригинальный язык и написание текста, ничего не переводи.\n"
        "- Один и тот же текст, висящий на нескольких кадрах, выписывай один раз.\n"
        "- Группируй по кадрам, указывая таймкод кадра.\n"
        "- Ничего не додумывай: пиши только то, что реально читается.\n"
        "- Если текста на кадрах нет вообще, ответь ровно: НЕТ ТЕКСТА"
    )
    content = _frames_as_content(frame_paths, instruction, duration)
    return await openai_chat(
        [{"role": "user", "content": content}],
        model=VISION_MODEL,
        max_tokens=3000,
        what="OpenAI Vision (OCR)",
    )


async def describe_frames_with_gpt(frame_paths: list, duration: float = 0.0) -> str:
    """Описывает происходящее на кадрах: сцена, люди, действия, монтаж."""
    instruction = (
        "Перед тобой кадры из видео по порядку. Опиши, что происходит в кадре, "
        "на русском языке.\n\n"
        "Укажи:\n"
        "- Кто в кадре: люди, их количество, роли, узнаваемые личности (если уверен).\n"
        "- Где происходит действие: помещение, студия, сцена, улица, интерьер.\n"
        "- Что делают: действия, жесты, смена планов, что показывают крупным планом.\n"
        "- Жанр и формат: интервью, концерт, влог, репортаж, нарезка, реклама.\n"
        "- Как меняется картинка от кадра к кадру.\n\n"
        "Текст на экране пересказывать не нужно — его разбирают отдельно. "
        "Не выдумывай того, чего не видно на кадрах."
    )
    content = _frames_as_content(frame_paths, instruction, duration)
    return await openai_chat(
        [{"role": "user", "content": content}],
        model=VISION_MODEL,
        max_tokens=2000,
        what="OpenAI Vision (сцена)",
    )


def split_audio_ffmpeg(audio_path: str, out_dir: str, chunk_sec: int) -> list:
    """Режет аудио на куски по chunk_sec секунд. Возвращает пути по порядку."""
    os.makedirs(out_dir, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", audio_path, "-f", "segment",
         "-segment_time", str(chunk_sec), "-c", "copy",
         os.path.join(out_dir, "chunk_%03d.mp3")],
        capture_output=True, timeout=600,
    )
    return sorted(glob.glob(os.path.join(out_dir, "chunk_*.mp3")))


def _format_diarized(segments: list, offset_sec: float = 0.0) -> str:
    """Склеивает подряд идущие сегменты одного говорящего в реплики.

    API возвращает сегменты уровня нескольких слов, поэтому без склейки диалог
    выглядел бы как список обрывков вместо реплик.
    """
    turns: list[dict] = []
    for seg in segments:
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        speaker = seg.get("speaker") or "?"
        if turns and turns[-1]["speaker"] == speaker:
            turns[-1]["text"] += " " + text
        else:
            turns.append({
                "speaker": speaker,
                "text": text,
                "start": float(seg.get("start") or 0.0) + offset_sec,
            })
    lines = []
    for turn in turns:
        ts = int(turn["start"])
        lines.append(f"[{ts // 60:02d}:{ts % 60:02d}] Говорящий {turn['speaker']}: {turn['text'].strip()}")
    return "\n".join(lines)


async def _transcribe_chunk(path: str, model: str, offset_sec: float, hint: str) -> str:
    """Транскрибирует один кусок аудио. Diarize-модель отдаёт реплики по ролям."""
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    with open(path, "rb") as f:
        audio_bytes = f.read()

    diarize = "diarize" in model
    data = {"model": model}
    if diarize:
        data["response_format"] = "diarized_json"
        # Обязательный для diarize-моделей параметр: без него API отвечает 400.
        data["chunking_strategy"] = "auto"
    else:
        data["response_format"] = "json"
    if SUMMARY_LANG:
        data["language"] = SUMMARY_LANG
    # Подсказка помогает модели не терять имена собственные и термины, но
    # diarize-модели отвергают её с HTTP 400 «Prompt is not supported for
    # diarization models», а whisper-1 трактует иначе — шлём только обычным.
    if hint and not diarize and model != "whisper-1":
        data["prompt"] = hint

    async with httpx.AsyncClient(timeout=600) as client:
        resp = await client.post(
            f"{OPENAI_BASE_URL}/audio/transcriptions",
            headers=headers,
            files={"file": (os.path.basename(path), audio_bytes, "audio/mpeg")},
            data=data,
        )
        resp.raise_for_status()
        payload = resp.json()

    if diarize and payload.get("segments"):
        formatted = _format_diarized(payload["segments"], offset_sec)
        if formatted:
            return formatted
    return (payload.get("text") or "").strip()


async def transcribe_audio(audio_path: str, hint: str = "") -> str:
    """Распознаёт речь целиком, при необходимости разбивая аудио на куски.

    Порядок моделей: diarize (реплики по говорящим) → gpt-4o-transcribe →
    whisper-1. Прежний код звал только whisper-1 без языка и подсказки, из-за
    чего на музыке и шумной записи возвращал пару строк вместо разговора.
    """
    if not OPENAI_API_KEY:
        raise SummaryError("OPENAI_API_KEY не задан — распознавание речи недоступно")

    size = os.path.getsize(audio_path)
    duration = probe_duration(audio_path)
    tmp_chunk_dir = os.path.join(os.path.dirname(audio_path), "achunks")

    if size > WHISPER_SIZE_LIMIT or (duration and duration > AUDIO_CHUNK_SEC):
        chunks = await asyncio.to_thread(split_audio_ffmpeg, audio_path, tmp_chunk_dir, AUDIO_CHUNK_SEC)
        if not chunks:
            chunks = [audio_path]
    else:
        chunks = [audio_path]

    log.info("transcribe: chunks=%s duration=%.0fs size=%s", len(chunks), duration, size)

    last_err: Exception | None = None
    for model in [TRANSCRIBE_MODEL] + [m for m in TRANSCRIBE_FALLBACKS if m != TRANSCRIBE_MODEL]:
        try:
            results = await asyncio.gather(*[
                _transcribe_chunk(chunk, model, idx * AUDIO_CHUNK_SEC, hint)
                for idx, chunk in enumerate(chunks)
            ])
            text = "\n".join(part for part in results if part).strip()
            if text:
                log.info("transcribe: модель=%s chars=%s", model, len(text))
                return text
            last_err = SummaryError(f"{model} вернул пустую расшифровку")
            log.warning("transcribe: %s вернул пусто, пробую следующую модель", model)
        except Exception as e:
            body = ""
            if isinstance(e, httpx.HTTPStatusError) and e.response is not None:
                body = e.response.text[:300]
            log.warning("transcribe: модель %s не сработала: %s %s", model, e, body)
            last_err = e

    log.error("transcribe: все модели исчерпаны: %s", last_err)
    return ""


# === MTProto-клиент для больших файлов (лениво, один на процесс) ===
_mtproto_client = None
_mtproto_lock = asyncio.Lock()


async def _get_mtproto_client():
    """Возвращает запущенный Telethon-клиент, авторизованный токеном бота."""
    global _mtproto_client
    async with _mtproto_lock:
        if _mtproto_client is None or not _mtproto_client.is_connected():
            from telethon import TelegramClient
            client = TelegramClient(MTPROTO_SESSION, TELETHON_API_ID, TELETHON_API_HASH)
            await client.start(bot_token=BOT_TOKEN)
            _mtproto_client = client
    return _mtproto_client


async def download_via_mtproto(file_id: str, chat_id: int, message_id: int, dest_path: str):
    """Скачивает файл через MTProto (обход лимита Bot API 20 МБ).

    Два пути:
    1. По Bot API file_id — работает не всегда: Telethon не умеет парсить
       новые версии формата file_id и молча возвращает None.
    2. Через get_messages по chat_id/message_id. Требует access_hash чата
       в кэше сессии — он появляется, когда клиент ловит апдейт о самом
       сообщении, поэтому клиент держится подключённым постоянно, а здесь
       стоят ретраи на случай гонки с доставкой апдейта.
    """
    client = await _get_mtproto_client()

    try:
        result_path = await client.download_media(file_id, file=dest_path)
        if result_path and os.path.exists(dest_path):
            return
        log.warning("mtproto: download по file_id вернул пусто, пробую get_messages")
    except Exception:
        log.warning("mtproto: download по file_id упал, пробую get_messages", exc_info=True)

    last_err: Exception | None = None
    for _ in range(6):
        try:
            msg = await client.get_messages(chat_id, ids=message_id)
            if msg is not None and msg.media is not None:
                result_path = await client.download_media(msg, file=dest_path)
                if result_path and os.path.exists(dest_path):
                    return
                raise SummaryError("MTProto: файл не сохранился на диск")
            last_err = SummaryError("MTProto: сообщение без медиа или не найдено")
        except SummaryError:
            raise
        except Exception as e:  # ValueError «Could not find the input entity» и сетевые
            last_err = e
        await asyncio.sleep(1.5)

    log.error("mtproto: все попытки исчерпаны: %s", last_err)
    raise SummaryError("Не удалось скачать файл через MTProto")


async def summarize_video_file_and_reply(update: Update, file_id: str, file_name: str, file_size: int):
    trace_id = uuid.uuid4().hex[:8]
    user_id = update.effective_user.id

    BOT_API_LIMIT = 20 * 1024 * 1024   # лимит скачивания через Bot API
    size_mb = file_size // 1024 // 1024

    if file_size > MAX_FILE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"⚠️ Файл слишком большой ({size_mb} МБ). Максимум — {MAX_FILE_MB} МБ."
        )
        return

    use_mtproto = file_size > BOT_API_LIMIT
    if use_mtproto and not (TELETHON_API_ID and TELETHON_API_HASH):
        await update.message.reply_text(
            f"⚠️ Файл слишком большой ({size_mb} МБ).\n"
            "MTProto-скачивание не настроено (нет TELETHON_API_ID/HASH в .env) — "
            "пока лимит 20 МБ. Сожми видео или обрежь до нужного фрагмента."
        )
        return

    log.info("videofile.start trace=%s user=%s size=%s name=%s mtproto=%s",
             trace_id, user_id, file_size, file_name, use_mtproto)
    status_msg = await update.message.reply_text(
        f"⏳ Скачиваю видео ({size_mb} МБ)..." if use_mtproto else "⏳ Скачиваю видео..."
    )

    tmpdir = tempfile.mkdtemp(prefix="summvid_")
    video_path = os.path.join(tmpdir, "video.mp4")
    audio_path = os.path.join(tmpdir, "audio.mp3")

    try:
        # 1. Download from Telegram: до 20 МБ — Bot API, больше — MTProto (до 2 ГБ)
        if use_mtproto:
            await download_via_mtproto(
                file_id, update.effective_chat.id, update.effective_message.message_id, video_path
            )
        else:
            file_obj = await update.effective_message.get_bot().get_file(file_id)
            await file_obj.download_to_drive(video_path)
        log.info("videofile.downloaded trace=%s bytes=%s", trace_id, os.path.getsize(video_path))

        # 2. Кадры и аудио: кадры режем всегда, аудио — только если дорожка есть
        frames_dir = os.path.join(tmpdir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        video_has_audio = await asyncio.to_thread(has_audio_stream, video_path)
        duration = await asyncio.to_thread(probe_duration, video_path)

        await status_msg.edit_text("🔊 Извлекаю кадры и аудио..." if video_has_audio
                                  else "🖼 Аудиодорожки нет — извлекаю кадры...")
        extract_jobs = [asyncio.to_thread(extract_frames_ffmpeg, video_path, frames_dir)]
        if video_has_audio:
            extract_jobs.append(asyncio.to_thread(extract_audio_ffmpeg, video_path, audio_path))
        extract_results = await asyncio.gather(*extract_jobs)
        frame_paths = extract_results[0]
        log.info("videofile.frames trace=%s count=%s duration=%.0fs",
                 trace_id, len(frame_paths), duration)

        # 3. Три независимых анализа параллельно: речь, текст на экране, картинка
        await status_msg.edit_text("🎙 Распознаю речь, текст на экране и видеоряд...")
        hint = f"Видео: {file_name}." if file_name else ""
        jobs = {}
        if video_has_audio:
            log.info("videofile.audio trace=%s audio_bytes=%s", trace_id, os.path.getsize(audio_path))
            jobs["speech"] = transcribe_audio(audio_path, hint)
        if frame_paths:
            jobs["screen_text"] = ocr_frames(frame_paths, duration)
            jobs["visual"] = describe_frames_with_gpt(frame_paths, duration)

        if not jobs:
            raise SummaryError("Из файла не удалось извлечь ни звук, ни кадры")

        # return_exceptions: сбой OCR не должен ронять весь разбор, если речь распозналась
        done = await asyncio.gather(*jobs.values(), return_exceptions=True)
        collected: dict[str, str] = {}
        for key, value in zip(jobs.keys(), done):
            if isinstance(value, Exception):
                log.warning("videofile.%s trace=%s failed: %s", key, trace_id, value)
                collected[key] = ""
            else:
                collected[key] = value or ""

        speech = collected.get("speech", "")
        screen_text = collected.get("screen_text", "")
        visual = collected.get("visual", "")
        if screen_text.strip().upper().startswith("НЕТ ТЕКСТА"):
            screen_text = ""

        log.info("videofile.parts trace=%s speech=%s screen_text=%s visual=%s",
                 trace_id, len(speech), len(screen_text), len(visual))

        if not (speech or screen_text or visual):
            raise SummaryError("Не удалось распознать ни речь, ни текст на экране, ни видеоряд")

        # 4. Финальный пересказ — один проход сильной модели, без переписывания черновика
        await status_msg.edit_text("🤖 Собираю пересказ...")
        title = file_name or "Видеофайл"
        final_summary = await summarize_multimodal(
            title,
            speech[:MAX_TRANSCRIPT_CHARS],
            screen_text[:MAX_TRANSCRIPT_CHARS],
            visual[:MAX_TRANSCRIPT_CHARS],
        )
        log.info("videofile.summary.ok trace=%s chars=%s", trace_id, len(final_summary))

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
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
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

        # Субтитры/расшифровка ролика — такая же «речь», что и у видеофайла,
        # поэтому ссылки идут через тот же подробный пересказ в один проход.
        log.info("sum.summary.request trace=%s model=%s", trace_id, SUMMARY_MODEL)
        final_video_summary = await summarize_multimodal(
            title,
            content_text[:MAX_TRANSCRIPT_CHARS],
            video_url=url,
        )
        log.info("sum.summary.ok trace=%s chars=%s", trace_id, len(final_video_summary))

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
        "• YouTube / TikTok ссылка — подробный пересказ + анализ комментариев\n"
        "• Видеофайл (до 2 ГБ) — распознаю речь с разделением по говорящим, "
        "читаю текст на экране и описываю видеоряд\n\n"
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


async def _post_init(app):
    """Поднимает MTProto-клиент сразу при старте: подключённый клиент получает
    те же апдейты и кэширует access_hash чатов — без этого get_messages для
    больших файлов падал бы на первом же сообщении."""
    if TELETHON_API_ID and TELETHON_API_HASH:
        try:
            await _get_mtproto_client()
            log.info("MTProto-клиент запущен (большие файлы до %s МБ)", MAX_FILE_MB)
        except Exception:
            log.exception("Не удалось запустить MTProto-клиент — большие файлы будут недоступны")


def main():
    log.info("=== Запуск бота ===")
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()
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
