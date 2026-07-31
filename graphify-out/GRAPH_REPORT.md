# Graph Report - .  (2026-07-22)

## Corpus Check
- 2 files · ~6,399 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 59 nodes · 97 edges · 19 communities detected
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

## God Nodes (most connected - your core abstractions)
1. `SummaryError` - 12 edges
2. `summarize_video_file_and_reply()` - 9 edges
3. `summarize_video_and_reply()` - 9 edges
4. `allowed()` - 6 edges
5. `normalize_text()` - 6 edges
6. `build_content_text()` - 6 edges
7. `request_summary_with_fallback()` - 6 edges
8. `download_via_mtproto()` - 5 edges
9. `on_text()` - 5 edges
10. `request_grok_summary()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `build_content_text()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 2_
- `request_grok_summary()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 4_
- `request_openai_comments_summary()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 7_
- `_post_init()` --calls--> `Exception`  [EXTRACTED]
  summarizvid.py →   _Bridges community 0 → community 5_
- `cmd_sum()` --calls--> `allowed()`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 1 → community 7_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.24
Nodes (12): Exception, describe_frames_with_gpt(), download_via_mtproto(), extract_audio_ffmpeg(), Extract audio from video file, compress to mono mp3 64kbps., Send frames to GPT-4o-mini Vision and return description of video content., Transcribe audio file via OpenAI Whisper API. Returns plain text., Скачивает файл по Bot API file_id через MTProto (обход лимита Bot API 20 МБ). (+4 more)

### Community 1 - "Community 1"
Cohesion: 0.43
Nodes (4): allowed(), cmd_ping(), cmd_start(), on_video_file()

### Community 2 - "Community 2"
Cohesion: 0.38
Nodes (7): build_content_text(), extract_comments(), extract_youtube_video_id(), fetch_text_from_subtitles(), fetch_youtube_transcript(), normalize_text(), parse_subtitle_payload()

### Community 3 - "Community 3"
Cohesion: 0.6
Nodes (4): _make_handler(), _make_stream_handler(), Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/, setup_bot_logging()

### Community 4 - "Community 4"
Cohesion: 0.5
Nodes (5): build_video_summary_prompt(), Пробует Grok, при ошибке — фоллбэк на OpenAI., request_grok_summary(), request_openai_summary(), request_summary_with_fallback()

### Community 5 - "Community 5"
Cohesion: 0.5
Nodes (4): _get_mtproto_client(), _post_init(), Возвращает запущенный Telethon-клиент, авторизованный токеном бота., Поднимает MTProto-клиент сразу при старте: подключённый клиент получает     те ж

### Community 6 - "Community 6"
Cohesion: 0.67
Nodes (3): detect_platform(), get_url_from_text(), on_text()

### Community 7 - "Community 7"
Cohesion: 0.67
Nodes (3): cmd_sum(), request_openai_comments_summary(), summarize_video_and_reply()

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (2): has_audio_stream(), Return True if video has at least one audio stream.

### Community 9 - "Community 9"
Cohesion: 1.0
Nodes (2): extract_frames_ffmpeg(), Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.

### Community 10 - "Community 10"
Cohesion: 1.0
Nodes (1): Пробует Grok, при ошибке — фоллбэк на OpenAI.

### Community 11 - "Community 11"
Cohesion: 1.0
Nodes (1): Return True if video has at least one audio stream.

### Community 12 - "Community 12"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 13 - "Community 13"
Cohesion: 1.0
Nodes (1): Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.

### Community 14 - "Community 14"
Cohesion: 1.0
Nodes (1): Send frames to GPT-4o-mini Vision and return description of video content.

### Community 15 - "Community 15"
Cohesion: 1.0
Nodes (1): Transcribe audio file via OpenAI Whisper API. Returns plain text.

### Community 16 - "Community 16"
Cohesion: 1.0
Nodes (1): Пробует Grok, при ошибке — фоллбэк на OpenAI.

### Community 17 - "Community 17"
Cohesion: 1.0
Nodes (1): Extract audio from video file, compress to mono mp3 64kbps.

### Community 18 - "Community 18"
Cohesion: 1.0
Nodes (1): Transcribe audio file via OpenAI Whisper API. Returns plain text.

## Knowledge Gaps
- **19 isolated node(s):** `Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/`, `Пробует Grok, при ошибке — фоллбэк на OpenAI.`, `Return True if video has at least one audio stream.`, `Extract audio from video file, compress to mono mp3 64kbps.`, `Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.` (+14 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 8`** (2 nodes): `has_audio_stream()`, `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (2 nodes): `extract_frames_ffmpeg()`, `Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (1 nodes): `Пробует Grok, при ошибке — фоллбэк на OpenAI.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (1 nodes): `Return True if video has at least one audio stream.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 12`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (1 nodes): `Extract n_frames evenly-spaced JPEG frames. Returns sorted list of paths.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 14`** (1 nodes): `Send frames to GPT-4o-mini Vision and return description of video content.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (1 nodes): `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `Пробует Grok, при ошибке — фоллбэк на OpenAI.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (1 nodes): `Extract audio from video file, compress to mono mp3 64kbps.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (1 nodes): `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SummaryError` connect `Community 0` to `Community 1`, `Community 2`, `Community 4`, `Community 7`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `_post_init()` connect `Community 5` to `Community 0`, `Community 1`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `request_summary_with_fallback()` connect `Community 4` to `Community 0`, `Community 1`, `Community 7`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **What connects `Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/`, `Пробует Grok, при ошибке — фоллбэк на OpenAI.`, `Return True if video has at least one audio stream.` to the rest of the system?**
  _19 weakly-connected nodes found - possible documentation gaps or missing edges._