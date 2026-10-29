"""
shared/knowledge/selection.py

What a crawl will learn, laid out as the website's folders, so the customer
can leave out whole areas before paying: every queued or sorted-out source
with its expected cost, placed in the folder of its page. Files sit in the
folder of the page that links them, since their own paths
(/public/upload/assets/16161/…) say nothing about what they belong to.

recommend() asks Gemini once, after the sorting step, which folders are
probably not worth their cost. Unlike the sorting step it decides nothing:
the suggestions are shown with what they'd save and applied with one click.
"""
import json
import re
from urllib.parse import unquote, urlparse

from google.genai import types

from app.ai_models import TRIAGE_GEMINI_MODEL
from app.database.supabase_client import fetch_all, supabase
from app.knowledge.jobs import calibration, estimate_source, is_index_only, tokens_cost
from app.knowledge.audience import audience_of, wording
from app.knowledge.triage import MANUAL, _get_client
from app.logging_config import error_logger

MAX_SUGGESTIONS = 6
# folders offered to the model: the most expensive ones with a few sources at least
FOLDERS_FOR_MODEL = 150
MIN_FOLDER_SOURCES = 3
LANGUAGES = ("en", "de", "fr")


def _site(host: str | None) -> str:
    host = (host or "").lower()
    return host[4:] if host.startswith("www.") else host


def folder_of(url: str, start_host: str) -> str:
    """'/verwaltung/einwohnerrat' for a page; other hosts keep their name: '//shop.example.ch/a'."""
    u = urlparse(url)
    path = unquote(u.path or "/").rstrip("/") or "/"
    # "/politik.html" is the page of the folder "/politik/…", not a sibling of it,
    # and CMS routes like "/politik.html/2" belong there too
    path = re.sub(r"/index\.html?(?=/|$)", "", path)
    path = re.sub(r"\.html?(?=/|$)", "", path) or "/"
    host = _site(u.hostname)
    return path if host == start_host else f"//{host}{'' if path == '/' else path}"


def selection(job: dict) -> list[dict]:
    """Every source this crawl would learn or has set aside, with cost and folder."""
    job_id = job["id"]
    start_host = _site(urlparse(job.get("start_url") or "").hostname)
    sources = fetch_all(lambda: (
        supabase.table("tenant_sources")
        .select("id, source_type, source_location, title, content_tokens, file_pages, status, skip_reason")
        .eq("last_job_id", job_id).in_("status", ["QUEUED", "SKIPPED"]).order("id")
    ))
    parents = {
        t["url"]: t.get("parent_url")
        for t in fetch_all(lambda: (
            supabase.table("crawling_tasks").select("url, parent_url").eq("job_id", job_id).order("id")
        ))
    }
    cal = calibration()
    items = []
    for s in sources:
        url = s["source_location"]
        is_file = s["source_type"] != "URL"
        parent = parents.get(url) if is_file else None
        items.append({
            "id": s["id"],
            "url": url,
            "title": (s.get("title") or "").strip() or None,
            "kind": "file" if is_file else "page",
            "pages": s.get("file_pages"),
            "selected": s["status"] == "QUEUED",
            "reason": s.get("skip_reason"),
            "index_only": is_index_only(s),
            "cost": round(tokens_cost(*estimate_source(s, cal)), 4),
            "folder": folder_of(parent or url, start_host) if (parent or not is_file)
                      else folder_of(url.rsplit("/", 1)[0], start_host),
        })
    return items


def _ancestors(folder: str) -> list[str]:
    """'/a/b' → ['/a', '/a/b']; '//shop.x.ch/a' → ['//shop.x.ch', '//shop.x.ch/a']. The start page has none."""
    head, rest = "", folder
    if folder.startswith("//"):
        host, _, rest = folder[2:].partition("/")
        head = f"//{host}"
    parts = [p for p in rest.split("/") if p]
    return ([head] if head else []) + [head + "/" + "/".join(parts[:i]) for i in range(1, len(parts) + 1)]


def _folders(items: list[dict]) -> dict[str, dict]:
    """Folder → queued sources below it (the folder's own page included), with cost and examples."""
    folders: dict[str, dict] = {}
    for it in items:
        if not it["selected"]:
            continue
        for prefix in _ancestors(it["folder"]):
            f = folders.setdefault(prefix, {"count": 0, "cost": 0.0, "examples": [], "title": None})
            f["count"] += 1
            f["cost"] += it["cost"]
            if it["kind"] == "page" and it["folder"] == prefix:
                f["title"] = it["title"]
            elif len(f["examples"]) < 4 and it["title"]:
                f["examples"].append(it["title"][:70])
    return folders


_SCHEMA = {
    "type": "object",
    "properties": {
        "suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string"},
                    "name": {"type": "string", "description": "What a visitor would call this area, 2–5 words, "
                             "in the website's language, e.g. \"Parlamentarische Vorstösse\""},
                    "reason": {
                        "type": "object",
                        "properties": {lang: {"type": "string"} for lang in LANGUAGES},
                        "required": list(LANGUAGES),
                    },
                },
                "required": ["folder", "name", "reason"],
            },
        },
    },
    "required": ["suggestions"],
}

_INSTRUCTIONS = """You help the owner of a chatbot on the website of {site} keep the cost of
its knowledge base down. Its {people} ask it everyday questions: {questions}.

Obvious junk (old budgets, old minutes, expired announcements) was already sorted out. Below
are the folders of the website that are still going to be learned, with how many pages and
documents each contains, what learning them costs in CHF, and example titles.

Suggest up to {max} folders the owner could leave out to save money, because {people} will
rarely ask about them or because they cost a lot compared to their use: archives, detailed
reports, historical material, press releases, long series of similar documents. Prefer
folders that save a noticeable amount. Never suggest {core}. If nothing is worth
leaving out, return an empty list.

For each suggestion, give the folder exactly as listed and one short sentence (at most 20
words) saying what is in it and why it can be left out, in English (en), German (de) and
French (fr). German: Swiss spelling ("ss" instead of "ß") but proper umlauts (ä, ö, ü), never
"ae", "oe", "ue". Address the owner directly, plain language, no technical terms."""


def recommend(job: dict) -> list[dict]:
    """Up to MAX_SUGGESTIONS folders worth leaving out: [{folder, title, reason: {en, de, fr}}]. Never raises."""
    try:
        folders = _folders(selection(job))
        candidates = sorted(
            ((path, f) for path, f in folders.items() if f["count"] >= MIN_FOLDER_SOURCES),
            key=lambda pf: -pf[1]["cost"],
        )[:FOLDERS_FOR_MODEL]
        if not candidates:
            return []
        lines = [
            f"{path} | {f['count']} sources | CHF {f['cost']:.2f} | {f['title'] or ''} | {'; '.join(f['examples'])}"
            for path, f in candidates
        ]
        response = _get_client().models.generate_content(
            model=TRIAGE_GEMINI_MODEL,
            contents=[
                _INSTRUCTIONS.format(site=job.get("start_url") or "", max=MAX_SUGGESTIONS,
                                    **wording(audience_of(job.get("tenant_id")))),
                "FOLDERS (folder | sources | cost | folder page title | example titles):\n" + "\n".join(lines),
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_SCHEMA,
                temperature=0,
                max_output_tokens=8_000,
            ),
        )
        suggestions = json.loads(response.text or "{}").get("suggestions") or []
        out, seen = [], set()
        for s in suggestions:
            path = s.get("folder") if isinstance(s, dict) else None
            reason = s.get("reason") if isinstance(s, dict) else None
            if path not in folders or path in seen or not isinstance(reason, dict):
                continue
            seen.add(path)
            name = str(s.get("name") or "").strip()[:80] or None
            out.append({"folder": path, "title": folders[path]["title"] or name,
                        "reason": {lang: str(reason.get(lang) or "")[:300] for lang in LANGUAGES}})
        error_logger.info("selection: job %s, %d savings suggestions", job["id"], len(out))
        return out[:MAX_SUGGESTIONS]
    except Exception as e:
        error_logger.warning("selection: suggestions for job %s failed: %s", job.get("id"), e)
        return []


# ---------------------------------------------------------------------------
# Exclusion rules: what the customer left out stays out in later crawls
# ---------------------------------------------------------------------------
# Stored on the tenant (crawl_exclusions) as a short list:
#   {"path": "/politik/einwohnerrat", "exclude": true,  "title": …}   a folder
#   {"path": "/politik/einwohnerrat/aktuell", "exclude": false}       kept inside it
#   {"url": "https://…/x.pdf", "exclude": true, "title": …}           one source
# The exact URL wins, then the longest folder; nothing matching means "learn".

MAX_RULES = 500


def _under(folder: str, path: str) -> bool:
    return folder == path or folder.startswith(path.rstrip("/") + "/")


def is_excluded(rules: list[dict], url: str, folder: str) -> bool:
    for r in rules:
        if r.get("url") == url:
            return bool(r.get("exclude"))
    best = None
    for r in rules:
        path = r.get("path")
        if path and _under(folder, path) and (best is None or len(path) > len(best["path"])):
            best = r
    return bool(best and best.get("exclude"))


def rules_of(tenant_id: str) -> list[dict]:
    row = supabase.table("tenants").select("crawl_exclusions").eq("id", str(tenant_id)).limit(1).execute().data
    return list((row[0].get("crawl_exclusions") if row else None) or [])


def _set_status(job_id: int, ids: list[int], selected: bool) -> None:
    fields = {"status": "QUEUED", "skip_reason": None} if selected else {"status": "SKIPPED", "skip_reason": MANUAL}
    current = "SKIPPED" if selected else "QUEUED"
    for i in range(0, len(ids), 200):
        supabase.table("tenant_sources").update(fields) \
            .in_("id", ids[i:i + 200]).eq("last_job_id", job_id).eq("status", current).execute()


def apply_rules(job: dict) -> int:
    """
    End of a scan, before sorting: leaves out what the rules exclude, and takes
    back in what was left out by hand but no longer is (rule removed in the
    settings). Returns how many sources the rules left out. Never raises.
    """
    try:
        rules = rules_of(job["tenant_id"])
        items = selection(job)
        leave_out = [i["id"] for i in items if i["selected"] and is_excluded(rules, i["url"], i["folder"])]
        take_back = [i["id"] for i in items if not i["selected"] and i["reason"] == MANUAL
                     and not is_excluded(rules, i["url"], i["folder"])]
        _set_status(job["id"], leave_out, False)
        _set_status(job["id"], take_back, True)
        return len(leave_out)
    except Exception as e:
        error_logger.error("selection: applying exclusions to job %s failed: %s", job.get("id"), e, exc_info=True)
        return 0


def _set_rule(rules: list[dict], folders: dict[str, str], *, exclude: bool, path: str | None = None,
              url: str | None = None, title: str | None = None) -> list[dict]:
    """Smallest rule list that makes `path` (a folder) or `url` (one source) excluded or not."""
    if path is not None:
        # anything more specific below this folder is replaced by the decision for the whole folder
        rules = [r for r in rules if not (
            (r.get("path") and _under(r["path"], path))
            or (r.get("url") and _under(folders.get(r["url"]) or folder_of(r["url"], ""), path))
        )]
        if is_excluded(rules, "", path) != exclude:
            rules.append({"path": path, "exclude": exclude, "title": title})
    else:
        rules = [r for r in rules if r.get("url") != url]
        if is_excluded(rules, url, folders.get(url) or "") != exclude:
            rules.append({"url": url, "exclude": exclude, "title": title})
    return rules


def change_selection(job: dict, *, include: list[int] = (), exclude: list[int] = (),
                     include_folders: list[str] = (), exclude_folders: list[str] = (),
                     restore_folders: list[str] = ()) -> list[dict]:
    """
    The customer ticks or unticks sources or folders before learning. Updates
    this crawl and the tenant's rules, so the choice holds for later crawls.
    restore_folders undoes an exclusion: what was left out by hand comes back,
    what the sorting step set aside stays out. Returns the new rules.
    """
    items = selection(job)
    by_id = {i["id"]: i for i in items}
    folders = {i["url"]: i["folder"] for i in items}
    page_titles = {i["folder"]: i["title"] for i in items if i["kind"] == "page"}
    rules = rules_of(job["tenant_id"])
    queue, skip = set(), set()

    for path, wanted in [(p, True) for p in exclude_folders] + [(p, False) for p in include_folders]:
        rules = _set_rule(rules, folders, path=path, exclude=wanted, title=page_titles.get(path))
        (skip if wanted else queue).update(i["id"] for i in items if _under(i["folder"], path))
    for path in restore_folders:
        rules = _set_rule(rules, folders, path=path, exclude=False)
        queue.update(i["id"] for i in items if _under(i["folder"], path) and i["reason"] == MANUAL)
    for source_id, wanted in [(i, True) for i in exclude] + [(i, False) for i in include]:
        item = by_id.get(source_id)
        if not item:
            continue
        rules = _set_rule(rules, folders, url=item["url"], exclude=wanted, title=item["title"])
        (skip if wanted else queue).add(source_id)

    if len(rules) > MAX_RULES:
        raise ValueError("too many exclusion rules")
    supabase.table("tenants").update({"crawl_exclusions": rules}).eq("id", job["tenant_id"]).execute()
    _set_status(job["id"], sorted(skip - queue), False)
    _set_status(job["id"], sorted(queue - skip), True)
    return rules
