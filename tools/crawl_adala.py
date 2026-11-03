"""
Catalogue the laws published by Morocco's Ministry of Justice on adala.justice.gov.ma.

Walks the portal's public folder tree (Arabic and French) and writes metadata only to
data/adala_catalog.json: title, law number, type, theme, dates and the official file URL.
One request at a time with a pause, because this is a public service.

    python tools/crawl_adala.py
"""

from __future__ import annotations

import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://adala.justice.gov.ma"
OUT = Path(__file__).resolve().parent.parent / "data" / "adala_catalog.json"
PAUSE_S = 0.4
UA = "Mozilla/5.0 (compatible; Mizan-legal-catalog/1.0; +https://github.com/Bosaj/moroccan-law-ai)"
NEXT_DATA = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def fetch_content(lang: str, folder: int) -> dict:
    prefix = "/fr" if lang == "fr" else ""
    req = urllib.request.Request(f"{BASE}{prefix}/resources/{folder}", headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        html = r.read().decode("utf-8", "replace")
    match = NEXT_DATA.search(html)
    if not match:
        return {}
    return json.loads(match.group(1)).get("props", {}).get("pageProps", {}).get("content") or {}


def file_url(path: str) -> str:
    return f"{BASE}/api/{urllib.parse.quote(path.lstrip('/'))}"


def api_roots(lang: str) -> list[int]:
    req = urllib.request.Request(f"{BASE}/api/files/resources", headers={"User-Agent": UA, "accept-language": lang.upper()})
    with urllib.request.urlopen(req, timeout=60) as r:
        return [row["id"] for row in json.load(r)]


def main() -> int:
    catalog: dict[int, dict] = {}
    seen: set[tuple[str, int]] = set()
    for lang in ("ar", "fr"):
        queue = [(root, []) for root in api_roots(lang)]
        while queue:
            folder, trail = queue.pop(0)
            if (lang, folder) in seen:
                continue
            seen.add((lang, folder))
            try:
                content = fetch_content(lang, folder)
            except Exception as err:  # keep going: one failed folder must not lose the crawl
                print(f"  skip {lang}/{folder}: {err}", file=sys.stderr)
                continue
            name = content.get("name", "")
            path = [*trail, name]
            for sub in content.get("folders") or []:
                queue.append((sub["id"], path))
            for f in content.get("files") or []:
                if f.get("deleted") or f.get("type") != "PDF" or not f.get("path"):
                    continue
                catalog[f["id"]] = {
                    "id": f["id"],
                    "name": (f.get("name") or "").strip(),
                    "lang": lang,
                    "trail": path,
                    "url": file_url(f["path"]),
                    "updated": f.get("updatedAt"),
                }
            print(f"{lang} {folder:>5} {len(content.get('folders') or []):>3} folders {len(content.get('files') or []):>4} files  total={len(catalog)}", flush=True)
            time.sleep(PAUSE_S)
    OUT.write_text(json.dumps(list(catalog.values()), ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"wrote {len(catalog)} documents to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
