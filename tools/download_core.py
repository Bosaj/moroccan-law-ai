"""
Download the official PDFs of the laws listed in data/core_laws.json and report what each one holds.

Run with: python tools/download_core.py
Files go to data/adala_cache/<catalogue id>.pdf (git-ignored). A file already there is reused.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.pdf_articles import coverage, keep_main_sequence, split_articles  # noqa: E402

CACHE = os.path.join(ROOT, "data", "adala_cache")
PAUSE_SECONDS = 0.4


def fetch(url: str, target: str) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Mizan legal corpus builder)"})
    with urllib.request.urlopen(request, timeout=120) as response, open(target + ".part", "wb") as out:
        out.write(response.read())
    os.replace(target + ".part", target)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(CACHE, exist_ok=True)
    with open(os.path.join(ROOT, "data", "adala_catalog.json"), encoding="utf-8") as f:
        catalog = {row["id"]: row for row in json.load(f)}
    with open(os.path.join(ROOT, "data", "core_laws.json"), encoding="utf-8") as f:
        laws = json.load(f)
    for law in laws:
        for lang in ("ar", "fr"):
            doc_id = law.get(lang)
            if not doc_id:
                continue
            row = catalog[doc_id]
            path = os.path.join(CACHE, f"{doc_id}.pdf")
            if not os.path.exists(path):
                try:
                    fetch(row["url"], path)
                except OSError as exc:
                    print(f"{law['slug']:24} {lang} FAILED {exc}")
                    continue
                time.sleep(PAUSE_SECONDS)
            articles, chars = split_articles(path)
            kept = keep_main_sequence(articles)
            cov = coverage(kept)
            size = os.path.getsize(path) // 1024
            missing = cov["missing"]
            print(f"{law['slug']:24} {lang} {size:6} KB chars={chars:8} raw={len(articles):5} kept={cov['count']:5} {cov['first']}-{cov['last']} missing={len(missing)} {missing[:8]}", flush=True)


if __name__ == "__main__":
    main()
