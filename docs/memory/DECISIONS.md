# Decisions

Record only durable decisions that affect future work. Append new entries; do not
rewrite history silently.

## 2026-08-09 — Adopt file-based project memory

- Status: Accepted
- Decision: Keep durable Codex instructions in `AGENTS.md` and portable project
  context in `docs/memory/`.
- Rationale: The project must remain understandable when opened from another device
  without depending on a previous chat thread.
- Consequences: Material work should update current state and session handoff files;
  secrets and full transcripts must remain outside project memory.

## 2026-10-30 — Related links block via OpenAI web_search

- Status: Accepted
- Decision: Append a "Узнать больше" block (Yandex/Google search links built from an
  LLM-extracted main-topic query, plus up to 3 verified pages from the OpenAI
  Responses API `web_search` tool) to every summary. Pattern borrowed from the
  `posterrec` bot.
- Rationale: Plain LLM links are often hallucinated; web_search returns real URLs and
  each is additionally checked by an HTTP request. Search engines and the video's own
  URL are filtered out.
- Consequences: One extra OpenAI call (+ web-search fee) per video; failure never
  blocks the summary. Toggle `RELATED_LINKS`, model `RELATED_MODEL`.
