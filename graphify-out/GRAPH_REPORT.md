# Graph Report - summariz  (2026-08-24)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 78 nodes · 150 edges · 12 communities (8 shown, 4 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 14 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `81c4d569`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11

## God Nodes (most connected - your core abstractions)
1. `summarize_video_file_and_reply()` - 13 edges
2. `summarize_video_and_reply()` - 11 edges
3. `SummaryError` - 9 edges
4. `on_text()` - 8 edges
5. `openai_chat()` - 8 edges
6. `transcribe_audio()` - 7 edges
7. `build_content_text()` - 7 edges
8. `main()` - 7 edges
9. `summarize_multimodal()` - 7 edges
10. `normalize_text()` - 6 edges

## Surprising Connections (you probably didn't know these)
- `main()` --indirect_call--> `_post_init()`  [INFERRED]
  summarizvid.py → summarizvid.py  _Bridges community 2 → community 6_
- `build_content_text()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 1_
- `download_via_mtproto()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 6_
- `openai_chat()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 3_
- `request_grok_chat()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 5_

## Import Cycles
- None detected.

## Communities (12 total, 4 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.17
Nodes (15): Exception, extract_audio_ffmpeg(), extract_frames_ffmpeg(), has_audio_stream(), probe_duration(), Return True if video has at least one audio stream., Extract audio from video file, compress to mono mp3 64kbps., Длительность медиафайла в секундах (0.0, если ffprobe не смог). (+7 more)

### Community 1 - "Community 1"
Cohesion: 0.38
Nodes (11): build_content_text(), detect_platform(), extract_comments(), extract_youtube_video_id(), fetch_media_info(), fetch_text_from_subtitles(), fetch_youtube_transcript(), normalize_text() (+3 more)

### Community 2 - "Community 2"
Cohesion: 0.47
Nodes (10): DEFAULT_TYPE, allowed(), cmd_ping(), cmd_start(), cmd_sum(), get_url_from_text(), main(), on_text() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.22
Nodes (10): describe_frames_with_gpt(), _frames_as_content(), ocr_frames(), openai_chat(), True для моделей, которые не принимают max_tokens (семейства gpt-5 и o-*)., Единая точка вызова OpenAI chat/completions с разбором ошибок. Сам подставляет…, Собирает content-массив для vision-запроса: инструкция + кадры с таймкодами., Распознаёт весь текст, видимый на кадрах. Отдельный проход, а не пункт в общем… (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.43
Nodes (6): _make_handler(), _make_stream_handler(), Simple logging setup for summarizvid bot. Creates rotating log files in ./logs/…, setup_bot_logging(), Logger, Path

### Community 5 - "Community 5"
Cohesion: 0.33
Nodes (6): build_multimodal_prompt(), Запрос к Grok с готовыми промптами. Живёт только при USE_GROK=1., Промпт финального пересказа видеофайла. Главное отличие от старого…, Финальный пересказ видео одним проходом сильной модели. Раньше здесь стояла…, request_grok_chat(), summarize_multimodal()

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (6): download_via_mtproto(), _get_mtproto_client(), _post_init(), Поднимает MTProto-клиент сразу при старте: подключённый клиент получает те же…, Возвращает запущенный Telethon-клиент, авторизованный токеном бота., Скачивает файл через MTProto (обход лимита Bot API 20 МБ). Два пути: 1. По Bot…

### Community 7 - "Community 7"
Cohesion: 0.50
Nodes (4): _format_diarized(), Склеивает подряд идущие сегменты одного говорящего в реплики. API возвращает…, Транскрибирует один кусок аудио. Diarize-модель отдаёт реплики по ролям., _transcribe_chunk()

## Knowledge Gaps
- **4 isolated node(s):** `start.sh script`, `stop.sh script`, `install.sh script`, `restart.sh script`
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `setup_bot_logging()` connect `Community 4` to `Community 1`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `summarize_video_file_and_reply()` connect `Community 0` to `Community 1`, `Community 2`, `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `SummaryError` connect `Community 0` to `Community 1`, `Community 3`, `Community 5`, `Community 6`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `summarize_video_file_and_reply()` (e.g. with `extract_audio_ffmpeg()` and `extract_frames_ffmpeg()`) actually correct?**
  _`summarize_video_file_and_reply()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `summarize_video_and_reply()` (e.g. with `build_content_text()` and `extract_comments()`) actually correct?**
  _`summarize_video_and_reply()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `start.sh script`, `stop.sh script`, `install.sh script` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
