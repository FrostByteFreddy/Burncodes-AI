"""
backend/scripts/dedupe_sources.py

One-off cleanup of duplicate tenant_sources rows created by the old crawler
(tasks were re-queued every 30 s and each copy indexed the page again).

For every (tenant, location) with more than one row, keeps one row — the
newest COMPLETED one, else the newest — and deletes the others together with
their File Search documents. Afterwards re-apply the schema migration so the
unique index on (tenant_id, source_location) is created.

Usage (from the repo root, with the production .env):
    python backend/scripts/dedupe_sources.py            # dry run: report only
    python backend/scripts/dedupe_sources.py --execute  # delete
"""
import argparse
import os
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv
from google import genai
from supabase import create_client

PAGE = 1000


def fetch_all(client) -> list[dict]:
    rows, start = [], 0
    while True:
        batch = (
            client.table("tenant_sources")
            .select("id, tenant_id, source_location, status, gemini_document_name, gemini_document_names")
            .order("id").range(start, start + PAGE - 1).execute()
        ).data or []
        rows += batch
        if len(batch) < PAGE:
            return rows
        start += PAGE


def plan(rows: list[dict]) -> tuple[list[dict], dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        groups[(r["tenant_id"], r["source_location"])].append(r)
    doomed, per_tenant = [], defaultdict(lambda: {"rows": 0, "documents": 0})
    for (tenant, _), group in groups.items():
        if len(group) < 2:
            continue
        completed = [r for r in group if r["status"] == "COMPLETED"]
        keep = max(completed or group, key=lambda r: r["id"])
        for r in group:
            if r["id"] == keep["id"]:
                continue
            doomed.append(r)
            per_tenant[tenant]["rows"] += 1
            per_tenant[tenant]["documents"] += len(doc_names(r))
    return doomed, per_tenant


def doc_names(row: dict) -> list[str]:
    names = list(row.get("gemini_document_names") or [])
    if row.get("gemini_document_name"):
        names.append(row["gemini_document_name"])
    return list(dict.fromkeys(names))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    parser.add_argument("--env", default=".env")
    args = parser.parse_args()

    load_dotenv(args.env)
    db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    rows = fetch_all(db)
    doomed, per_tenant = plan(rows)
    names = [n for r in doomed for n in doc_names(r)]

    tenants = {t["id"]: t["name"] for t in db.table("tenants").select("id, name").execute().data or []}
    print(f"{len(rows)} source rows, {len(doomed)} duplicates to remove, {len(names)} Gemini documents to delete")
    for tenant, stats in sorted(per_tenant.items(), key=lambda kv: -kv[1]["rows"]):
        print(f"  {tenants.get(tenant, tenant):<30} rows={stats['rows']:<6} documents={stats['documents']}")
    if not args.execute:
        print("Dry run — nothing deleted. Re-run with --execute.")
        return 0

    gclient = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    failed = []

    def delete_doc(name: str) -> None:
        # Same as GeminiStoreService.delete_document: a document with chunks
        # can't be deleted (FAILED_PRECONDITION), so purge its chunks first.
        try:
            chunks = [c.name for c in gclient.file_search_stores.documents.chunks.list(parent=name)]
            if chunks:
                gclient.file_search_stores.documents.chunks.batch_delete(parent=name, config={"names": chunks})
            gclient.file_search_stores.documents.delete(name=name)
        except Exception as e:
            if "404" not in str(e) and "NOT_FOUND" not in str(e):
                failed.append((name, str(e)[:200]))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(delete_doc, names))
    ids = [r["id"] for r in doomed]
    for i in range(0, len(ids), 200):
        db.table("tenant_sources").delete().in_("id", ids[i:i + 200]).execute()
    print(f"Deleted {len(ids)} rows and {len(names) - len(failed)} documents ({len(failed)} document deletions failed).")
    for name, err in failed[:10]:
        print("  failed:", name, err)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
