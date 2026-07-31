# Graph Report - .  (2026-07-31)

## Corpus Check
- 2 files · ~10,052 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 99 nodes · 118 edges · 42 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]

## God Nodes (most connected - your core abstractions)
1. `SummaryError` - 9 edges
2. `summarize_video_file_and_reply()` - 9 edges
3. `openai_chat()` - 8 edges
4. `summarize_video_and_reply()` - 8 edges
5. `summarize_multimodal()` - 7 edges
6. `allowed()` - 6 edges
7. `normalize_text()` - 6 edges
8. `build_content_text()` - 6 edges
9. `transcribe_audio()` - 6 edges
10. `ocr_frames()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `build_content_text()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 1 → community 3_
- `openai_chat()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 1 → community 2_
- `request_grok_chat()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 1 → community 4_
- `summarize_video_and_reply()` --calls--> `Exception`  [EXTRACTED]
  summarizvid.py →   _Bridges community 1 → community 0_
- `summarize_video_and_reply()` --calls--> `normalize_text()`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 3 → community 0_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.25
Nodes (11): allowed(), cmd_ping(), cmd_start(), cmd_sum(), detect_platform(), get_url_from_text(), on_text(), on_video_file() (+3 more)

### Community 1 - "Community 1"
Cohesion: 0.21
Nodes (13): Exception, download_via_mtproto(), extract_audio_ffmpeg(), _get_mtproto_client(), _post_init(), Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж, Extract audio from video file, compress to mono mp3 64kbps., Распознаёт речь целиком, при необходимости разбивая аудио на куски.      Порядок (+5 more)

### Community 2 - "Community 2"
Cohesion: 0.2
Nodes (11): describe_frames_with_gpt(), _frames_as_content(), ocr_frames(), openai_chat(), True для моделей, которые не принимают max_tokens (семейства gpt-5 и o-*)., Единая точка вызова OpenAI chat/completions с разбором ошибок.      Сам подставл, Собирает content-массив для vision-запроса: инструкция + кадры с таймкодами., Распознаёт весь текст, видимый на кадрах.      Отдельный проход, а не пункт в об (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.38
Nodes (7): build_content_text(), extract_comments(), extract_youtube_video_id(), fetch_text_from_subtitles(), fetch_youtube_transcript(), normalize_text(), parse_subtitle_payload()

### Community 4 - "Community 4"
Cohesion: 0.33
Nodes (6): build_multimodal_prompt(), Запрос к Grok с готовыми промптами. Живёт только при USE_GROK=1., Промпт финального пересказа видеофайла.      Главное отличие от старого build_vi, Финальный пересказ видео одним проходом сильной модели.      Раньше здесь стояла, request_grok_chat(), summarize_multimodal()

### Community 5 - "Community 5"
Cohesion: 0.6
Nodes (4): _make_handler(), _make_stream_handler(), Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/, setup_bot_logging()

### Community 6 - "Community 6"
Cohesion: 0.5
Nodes (4): _format_diarized(), Склеивает подряд идущие сегменты одного говорящего в реплики.      API возвращае, Транскрибирует один кусок аудио. Diarize-модель отдаёт реплики по ролям., _transcribe_chunk()

### Community 7 - "Community 7"
Cohesion: 0.5
Nodes (4): extract_frames_ffmpeg(), probe_duration(), Длительность медиафайла в секундах (0.0, если ffprobe не смог)., Нарезает кадры примерно раз в VISION_FRAME_EVERY_SEC секунд.      Раньше бралось

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (2): has_audio_stream(), Return True if video has at least one audio stream.

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (1): Финальный пересказ видео одним проходом сильной модели.      Раньше здесь стояла

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): Return True if video has at least one audio stream.

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (1): Длительность медиафайла в секундах (0.0, если ffprobe не смог).

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (1): Нарезает кадры примерно раз в VISION_FRAME_EVERY_SEC секунд.      Раньше бралось

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): Собирает content-массив для vision-запроса: инструкция + кадры с таймкодами.

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Распознаёт весь текст, видимый на кадрах.      Отдельный проход, а не пункт в об

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Описывает происходящее на кадрах: сцена, люди, действия, монтаж.

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Режет аудио на куски по chunk_sec секунд. Возвращает пути по порядку.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Склеивает подряд идущие сегменты одного говорящего в реплики.      API возвращае

### Community 19 - "Community 19"
Cohesion: 1.0
Nodes (1): Транскрибирует один кусок аудио. Diarize-модель отдаёт реплики по ролям.

### Community 20 - "Community 20"
Cohesion: 1.0
Nodes (1): Распознаёт речь целиком, при необходимости разбивая аудио на куски.      Порядок

### Community 21 - "Community 21"
Cohesion: 1.0
Nodes (1): Возвращает запущенный Telethon-клиент, авторизованный токеном бота.

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Скачивает файл через MTProto (обход лимита Bot API 20 МБ).      Два пути:     1.

### Community 23 - "Community 23"
Cohesion: 1.0
Nodes (1): Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж

### Community 24 - "Community 24"
Cohesion: 1.0
Nodes (1): Пробует Grok, при ошибке — фоллбэк на OpenAI.

### Community 25 - "Community 25"
Cohesion: 1.0
Nodes (1): Return True if video has at least one audio stream.

### Community 26 - "Community 26"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 27 - "Community 27"
Cohesion: 1.0
Nodes (1): Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Send frames to GPT-4o-mini Vision and return description of video content.

### Community 29 - "Community 29"
Cohesion: 1.0
Nodes (1): Transcribe audio file via OpenAI Whisper API. Returns plain text.

### Community 30 - "Community 30"
Cohesion: 1.0
Nodes (1): Возвращает запущенный Telethon-клиент, авторизованный токеном бота.

### Community 31 - "Community 31"
Cohesion: 1.0
Nodes (1): Скачивает файл по Bot API file_id через MTProto (обход лимита Bot API 20 МБ).

### Community 32 - "Community 32"
Cohesion: 1.0
Nodes (1): Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж

### Community 33 - "Community 33"
Cohesion: 1.0
Nodes (1): Пробует Grok, при ошибке — фоллбэк на OpenAI.

### Community 34 - "Community 34"
Cohesion: 1.0
Nodes (1): Return True if video has at least one audio stream.

### Community 35 - "Community 35"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 36 - "Community 36"
Cohesion: 1.0
Nodes (1): Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.

### Community 37 - "Community 37"
Cohesion: 1.0
Nodes (1): Send frames to GPT-4o-mini Vision and return description of video content.

### Community 38 - "Community 38"
Cohesion: 1.0
Nodes (1): Transcribe audio file via OpenAI Whisper API. Returns plain text.

### Community 39 - "Community 39"
Cohesion: 1.0
Nodes (1): Пробует Grok, при ошибке — фоллбэк на OpenAI.

### Community 40 - "Community 40"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 41 - "Community 41"
Cohesion: 1.0
Nodes (1): Transcribe audio file via OpenAI Whisper API. Returns plain text.

## Knowledge Gaps
- **53 isolated node(s):** `Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/`, `True для моделей, которые не принимают max_tokens (семейства gpt-5 и o-*).`, `Единая точка вызова OpenAI chat/completions с разбором ошибок.      Сам подставл`, `Запрос к Grok с готовыми промптами. Живёт только при USE_GROK=1.`, `Промпт финального пересказа видеофайла.      Главное отличие от старого build_vi` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 8`** (2 nodes): `has_audio_stream()`, `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (1 nodes): `Финальный пересказ видео одним проходом сильной модели.      Раньше здесь стояла`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (1 nodes): `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `Длительность медиафайла в секундах (0.0, если ffprobe не смог).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `Нарезает кадры примерно раз в VISION_FRAME_EVERY_SEC секунд.      Раньше бралось`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `Собирает content-массив для vision-запроса: инструкция + кадры с таймкодами.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Распознаёт весь текст, видимый на кадрах.      Отдельный проход, а не пункт в об`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Описывает происходящее на кадрах: сцена, люди, действия, монтаж.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `Режет аудио на куски по chunk_sec секунд. Возвращает пути по порядку.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Склеивает подряд идущие сегменты одного говорящего в реплики.      API возвращае`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (1 nodes): `Транскрибирует один кусок аудио. Diarize-модель отдаёт реплики по ролям.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (1 nodes): `Распознаёт речь целиком, при необходимости разбивая аудио на куски.      Порядок`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (1 nodes): `Возвращает запущенный Telethon-клиент, авторизованный токеном бота.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (1 nodes): `Скачивает файл через MTProto (обход лимита Bot API 20 МБ).      Два пути:     1.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (1 nodes): `Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `Пробует Grok, при ошибке — фоллбэк на OpenAI.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 25`** (1 nodes): `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 26`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 27`** (1 nodes): `Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (1 nodes): `Send frames to GPT-4o-mini Vision and return description of video content.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 29`** (1 nodes): `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 30`** (1 nodes): `Возвращает запущенный Telethon-клиент, авторизованный токеном бота.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 31`** (1 nodes): `Скачивает файл по Bot API file_id через MTProto (обход лимита Bot API 20 МБ).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 32`** (1 nodes): `Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (1 nodes): `Пробует Grok, при ошибке — фоллбэк на OpenAI.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 34`** (1 nodes): `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 35`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 36`** (1 nodes): `Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 37`** (1 nodes): `Send frames to GPT-4o-mini Vision and return description of video content.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `Пробует Grok, при ошибке — фоллбэк на OpenAI.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 41`** (1 nodes): `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `openai_chat()` connect `Community 2` to `Community 0`, `Community 1`, `Community 4`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `summarize_multimodal()` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `_post_init()` connect `Community 1` to `Community 0`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/`, `True для моделей, которые не принимают max_tokens (семейства gpt-5 и o-*).`, `Единая точка вызова OpenAI chat/completions с разбором ошибок.      Сам подставл` to the rest of the system?**
  _53 weakly-connected nodes found - possible documentation gaps or missing edges._