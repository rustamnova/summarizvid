# Graph Report - .  (2026-04-27)

## Corpus Check
- 1 files · ~7,518 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 33 nodes · 72 edges · 6 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]

## God Nodes (most connected - your core abstractions)
1. `SummaryError` - 10 edges
2. `summarize_video_and_reply()` - 9 edges
3. `summarize_video_file_and_reply()` - 7 edges
4. `allowed()` - 6 edges
5. `normalize_text()` - 6 edges
6. `build_content_text()` - 6 edges
7. `request_summary_with_fallback()` - 6 edges
8. `on_text()` - 5 edges
9. `request_grok_summary()` - 4 edges
10. `request_openai_summary()` - 4 edges

## Surprising Connections (you probably didn't know these)
- `build_content_text()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 1_
- `request_grok_summary()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 3_
- `request_openai_comments_summary()` --calls--> `SummaryError`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 0 → community 5_
- `cmd_sum()` --calls--> `allowed()`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 2 → community 5_
- `on_text()` --calls--> `allowed()`  [EXTRACTED]
  summarizvid.py → summarizvid.py  _Bridges community 2 → community 4_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.36
Nodes (8): Exception, extract_audio_ffmpeg(), Extract audio from video file, compress to mono mp3 64kbps., Transcribe audio file via OpenAI Whisper API. Returns plain text., request_openai_rewrite(), summarize_video_file_and_reply(), SummaryError, transcribe_with_whisper()

### Community 1 - "Community 1"
Cohesion: 0.38
Nodes (7): build_content_text(), extract_comments(), extract_youtube_video_id(), fetch_text_from_subtitles(), fetch_youtube_transcript(), normalize_text(), parse_subtitle_payload()

### Community 2 - "Community 2"
Cohesion: 0.43
Nodes (4): allowed(), cmd_ping(), cmd_start(), on_video_file()

### Community 3 - "Community 3"
Cohesion: 0.5
Nodes (5): build_video_summary_prompt(), Пробует Grok, при ошибке — фоллбэк на OpenAI., request_grok_summary(), request_openai_summary(), request_summary_with_fallback()

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (3): detect_platform(), get_url_from_text(), on_text()

### Community 5 - "Community 5"
Cohesion: 0.67
Nodes (3): cmd_sum(), request_openai_comments_summary(), summarize_video_and_reply()

## Knowledge Gaps
- **3 isolated node(s):** `Пробует Grok, при ошибке — фоллбэк на OpenAI.`, `Extract audio from video file, compress to mono mp3 64kbps.`, `Transcribe audio file via OpenAI Whisper API. Returns plain text.`
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `request_summary_with_fallback()` connect `Community 3` to `Community 0`, `Community 2`, `Community 5`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `extract_audio_ffmpeg()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `transcribe_with_whisper()` connect `Community 0` to `Community 2`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **What connects `Пробует Grok, при ошибке — фоллбэк на OpenAI.`, `Extract audio from video file, compress to mono mp3 64kbps.`, `Transcribe audio file via OpenAI Whisper API. Returns plain text.` to the rest of the system?**
  _3 weakly-connected nodes found - possible documentation gaps or missing edges._