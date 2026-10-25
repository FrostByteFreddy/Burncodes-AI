# Graph RAG for SwiftAnswer — design

Status: proposal (2026-10-24). Replaces Gemini File Search as the retrieval
engine with a knowledge graph, and fixes date/table questions at ingestion.

## 1. What we need to get right

Tenants are municipalities and organisations. Their knowledge is ~12k crawled
web pages, ~10.7k linked files (1.8k PDFs) and uploads. The questions that
matter most are often **facts locked in layout**: collection calendars, opening
hours, fee tables, event dates.

Tested on Zofingen's *Abfallkalender 2025* (2-page InDesign PDF):

| Approach | Result |
|---|---|
| Plain text extraction (what every indexer sees today) | Row labels first, then `Jan 6. 13. 20. 27. Feb 3. …` — dates detached from category/zone; red "exception" colour lost. **No retrieval method can recover this afterwards** — vector, File Search or graph. |
| Gemini 2.5 Flash, PDF → JSON | Row bleed (Zone 2 dates in Zone 1), 10 wrong exception flags, wrong Litter-Ritter months. |
| **Gemini 4 (`gemini-4-argon`), PDF → JSON + validation** | **All 155 grid dates and all 6 red exceptions correct; 0 validation problems.** ~6.9k in / 4.2k out tokens. Missed one rule-based line ("Bottenstein: Mittwoch vor Monatsmarkt"). |
| Text-layer geometry (pdfplumber: x/y + glyph colour) | Exact for rows it could locate; needs per-layout tuning → use as a cross-check, not as the extractor. |

Conclusion: **the graph is the retrieval layer, but date correctness is decided at
ingestion.** Schedules become validated structured records; everything else
becomes graph knowledge.

## 2. Architecture

```
                       ┌──────────────── ingestion (worker_fast / worker_heavy) ────────────────┐
 web page ─ crawl ───▶ │ clean markdown ──────────────────────────────┐                         │
 PDF/DOCX/image ─────▶ │ document understanding (INDEXING_GEMINI_MODEL, page vision)            │
                       │   ├─ markdown with real tables + figure captions ──┐                    │
                       │   └─ schedule records (series, zone, date, exception) ─▶ validate ─┐   │
                       │                                                    ▼               ▼   │
                       │                              LightRAG insert (graph+vectors)   events  │
                       └──────────────────────────────────────┬──────────────────────────┬────┘
                                                              │ workspace = tenant_id    │
                                                  Postgres: LIGHTRAG_* tables,     tenant_events
                                                  lightrag_graph_nodes/edges (no AGE), pgvector
                                                              │                          │
 chat ─▶ worker_chat (CHAT_GEMINI_MODEL, function calling, today's date in prompt)       │
           ├─ tool search_knowledge(query)  → LightRAG aquery_data (mix mode, capped)    │
           └─ tool find_dates(series?, zone?, from?, to?) → SQL ─────────────────────────┘
           answer + citations + billing stay in our code
```

### 2.1 Graph engine: LightRAG (1.5.x) as a library

Researched alternatives and why they lose for us:

| Option | Verdict |
|---|---|
| **LightRAG 1.5.x** | ✅ Incremental inserts, **delete by document with graph rebuild** (we re-crawl and delete constantly), mix mode = graph + vector chunks, Gemini LLM + embedding bindings, Postgres for all four storages. RAG-Anything (multimodal parsing) is merged into it since 1.5. |
| Microsoft GraphRAG | ❌ Community-report indexing is expensive and effectively re-indexes on change; bad fit for re-crawled sites. |
| LazyGraphRAG | ➖ Cheap indexing, but query-time cost/latency shift; less mature integration story. |
| Graphiti (Zep) | ❌ Built for temporal agent memory (episodes), needs Neo4j/FalkorDB. |
| Neo4j GraphRAG package | ❌ Toolkit, not a system; needs Neo4j; we'd build what LightRAG already has. |

Facts verified in LightRAG's source (commit `aaebfe1`, 2026-10-14):

- `PGTableGraphStorage` stores the graph in two plain tables
  (`lightrag_graph_nodes`, `lightrag_graph_edges`, JSONB + B-tree) — **no Apache
  AGE**, runs on any PostgreSQL 14+. Recommended over the AGE backend since v1.5.6.
- Postgres storages isolate tenants with a `workspace` column. One `LightRAG`
  instance = one workspace; instances share one connection pool (`ClientManager`
  is a class-level singleton), so a worker can hold one instance per tenant.
- `aquery_data()` returns entities, relations and chunks **without generating an
  answer** → we keep our own prompt, fine-tune rules, billing and citations.
- Query defaults are large: `top_k=40`, `chunk_top_k=20`, entity/relation/total
  token budgets 6k/8k/30k. We cap them (§4).
- Extraction prompt ≈ 2.1k tokens of instructions per chunk; default chunk 1200
  tokens; `MAX_GLEANING=1` (a second "continue extraction" call per chunk).
- Query does one extra LLM call for keyword extraction (~0.7k tokens).
- The LightRAG **API server** is one workspace per process → we embed the
  library in our workers instead of running the server.

### 2.2 Storage: dedicated Postgres, not the Supabase app DB

LightRAG creates ~13 tables and needs pgvector. Rough size for the current
corpus: ~30k chunks + ~300–500k entities/relations vectors. At 3072 dims that's
several GB of vectors plus HNSW indexes; at 768 dims (Gemini embeddings support
`output_dimensionality`) about a quarter. Keep it out of the app database:

- **Recommended:** a `graphdb` Postgres 17 + pgvector container in
  `docker-compose.prod.yml`, nightly `pg_dump`, not exposed publicly.
- Alternative: a second Supabase project (managed backups, costs a plan).

### 2.3 Ingestion

1. **Route by content type.**
   - Web pages: today's extractor → markdown → `ainsert`.
   - PDF / DOCX / images: **document understanding** with
     `INDEXING_GEMINI_MODEL` (Gemini 4). One call per document (or per page
     range for long docs) returning:
     - `markdown`: faithful text, tables as Markdown tables, figure/map captions;
     - `schedules`: series → dates (schema as in the prototype), plus rules
       that aren't dates ("Mittwoch vor Monatsmarkt") as text;
     - `facts`: opening hours, fees, contacts as key/value rows.
2. **Validate schedules deterministically** before trusting them:
   - every date on the series' printed weekday unless flagged as exception;
     every flagged exception off the regular weekday;
   - no duplicate dates; plausible per-month counts;
   - born-digital PDFs: each extracted day number must exist in that month's
     column of the text layer (pdfplumber), i.e. two independent readings agree;
   - on failure: retry with the page image at higher DPI; still failing →
     index markdown only and mark the source `NEEDS_REVIEW` in the dashboard.
3. **Store** valid records in `tenant_events` (one row per date) and insert
   the markdown into LightRAG with `ids=[source_id]` so `adelete_by_doc_id`
   removes exactly that source's contribution on re-crawl/delete.
4. **Validity window:** each schedule carries its year/valid-from–to. A
   document for 2025 must not answer "next pickup" in 2026 (see §3).

### 2.4 Query

The chat worker switches to Gemini **function calling** with two tools:

- `search_knowledge(query)` → `aquery_data(mode="mix")` with capped budgets;
  results become the context and citations.
- `find_dates(series?, zone?, date_from?, date_to?)` → SQL on `tenant_events`
  for the tenant. Deterministic answers for "wann", "nächste", "diese Woche".

The system prompt always states **today's date**, so the model resolves
"nächsten Dienstag" correctly and can say "der Kalender gilt für 2025 — für 2026
liegt noch kein Kalender vor".

**Zones by street:** in Zofingen the street→zone mapping exists only as a map.
Reading a street map with a VLM is not reliable enough. The bot asks for the
zone (Zone 1 = Montag, Zone 2 = Freitag) and links the map/PDF; tenants can add
a street list as custom knowledge, which then becomes `facts`.

## 3. Date questions this must pass (acceptance tests)

With "today" fixed per test case:

| Today | Question | Expected |
|---|---|---|
| 2025-04-14 | Wann ist die nächste Kehrichtabfuhr in Zone 1? | Mi 23.04.2025 (Ausnahme, statt Montag) |
| 2025-07-28 | Zone 2 diese Woche? | Do 31.07.2025 (Ausnahme) |
| 2025-02-01 | Nächste Papiersammlung? | Mi 19.02.2025, ab 07:00 beim Kehrichtsammelort |
| 2025-12-20 | Grünabfuhr noch im Dezember? | Di 09.12. war die letzte → keine mehr 2025 |
| 2025-04-01 | Wann ist der Häckseldienst? | 1.–3. April und 28.–30. Oktober, Anmeldung beim Werkhof |
| 2026-10-24 | Nächste Kehrichtabfuhr Zone 1? | States the calendar is 2025-only; no invented 2026 date |
| any | Wo kann ich Batterien abgeben? | Verkaufsstellen / Gloor Recycling Center (graph question) |

These go into an eval script alongside ~30 non-date questions per pilot tenant;
File Search and the graph engine run side by side until the graph wins.

## 4. Cost model (tokens; plug in current Gemini prices)

Assumptions: ~33M source tokens today (12k pages × ~2k, 1.8k PDFs × ~5k), chunk
1200 tokens → ~28k chunks.

| Step | Tokens | Notes |
|---|---|---|
| Graph extraction, full corpus, gleaning=1 | ~225M in / ~34M out | one-off; `MAX_GLEANING=0` roughly halves it |
| Document understanding (PDFs) | ~3.5k in + ~2k out per page | only for files, measured on the Zofingen PDF |
| Embeddings | ~35M + entity/relation descriptions | cheap |
| **Per chat message** | ~0.8k (keywords) + ≤8k context | vs **median 659** today |

Per-message input grows ~10×. At today's chat rate (8 CHF/1M input) a message
would cost tenants ~0.07–0.08 CHF instead of ~0.016. Before launch, either cap
context tighter, lower `CHAT_RATE_CHF_PER_1M_INPUT`, or move chat to
per-message pricing. All rates/models are env-configurable
(`backend/shared/ai_models.py`).

Query budget to start with: `top_k=20`, `chunk_top_k=8`,
`max_entity_tokens=1500`, `max_relation_tokens=1500`, `max_total_tokens=8000`.

## 5. Rollout

1. **Pilot ingestion (no engine switch):** document understanding + validation +
   `tenant_events` + `find_dates` tool on top of today's File Search. Fixes
   calendar questions immediately and is independent of the graph decision.
2. **Graph engine behind a flag:** `tenants.rag_engine = 'file_search' | 'graph'`,
   graph Postgres container, LightRAG ingestion in workers, `search_knowledge`
   tool. Index 1–2 pilot tenants (Zofingen-like + one web-only).
3. **Eval:** run §3 + per-tenant question sets on both engines; compare answer
   quality, latency, cost per message.
4. **Migrate** tenants that win; re-crawl schedule keeps the graph fresh via
   delete-by-doc + insert.

## 6. Open decisions

- Graph DB hosting: container on the Hetzner box vs second Supabase project.
- Model for bulk graph extraction across ~28k chunks: Gemini 4 everywhere, or a
  cheaper flash model for web pages and Gemini 4 only for documents
  (add `GRAPH_EXTRACT_GEMINI_MODEL`).
- Chat pricing once context is ~10× larger.
