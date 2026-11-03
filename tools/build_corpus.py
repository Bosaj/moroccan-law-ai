"""
Build data/corpus.sqlite: every article of the laws in data/core_laws.json, cut from the official PDFs,
plus a searchable list of all documents the ministry publishes (data/adala_catalog.json).

Run tools/crawl_adala.py to refresh the catalogue, tools/download_core.py to fetch the PDFs, then this.
Also writes data/corpus_report.json, which lists gaps in each law's numbering for a person to review.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pymupdf  # noqa: E402

from src.legal_text import stems  # noqa: E402
from src.pdf_articles import Article, coverage, keep_main_sequence, page_lines, split_articles  # noqa: E402

CACHE = os.path.join(ROOT, "data", "adala_cache")
TARGET = os.path.join(ROOT, "data", "corpus.sqlite")
REPORT = os.path.join(ROOT, "data", "corpus_report.json")

_CONSOLIDATED = re.compile(r"(?:صيغة\s+محينة\s+بتاريخ|Version\s+consolid[ée]e\s+en\s+date\s+du|Version\s+consolid[ée]e\s+du)\s*(.{4,40})", re.IGNORECASE)
_DAHIR = re.compile(r"(?:ظهير\s+شريف\s+(?:بمثابة\s+قانون\s+)?(?:رقم\s+)|Dahir\s+(?:portant\s+loi\s+)?n°\s*)([\d]+[.\-][\d]+[.\-][\d]+)", re.IGNORECASE)
_BO = re.compile(r"(?:الجريدة\s+الرسمية\s+عدد|bulletin\s+officiel(?:\s+en\s+arabe)?\s+n°|B\.?O\.?\s+n°)\s*([\d]{3,5})", re.IGNORECASE)
_LIST_ITEM = re.compile(r"^\s*(?:[-–—•]|\d+[.)\-]|[أ-ي][.)\-]\s|أولا|ثانيا|ثالثا|رابعا|خامسا|[a-z]\))")
_ENDS_PARAGRAPH = re.compile(r"[.:؛;؟?!]\s*$")
# Bullets drawn with a symbol font come through as private-use characters
SYMBOL_FONT = str.maketrans({"": "-", "": "-"})


def reflow(text: str) -> str:
    """Join the lines of a printed page back into paragraphs. Words are left exactly as printed."""
    paragraphs: list[str] = []
    for raw in text.translate(SYMBOL_FONT).split("\n"):
        line = raw.strip()
        if not line:
            continue
        if paragraphs and not _ENDS_PARAGRAPH.search(paragraphs[-1]) and not _LIST_ITEM.match(line):
            if paragraphs[-1].endswith("-") and line[0].islower():
                paragraphs[-1] = paragraphs[-1][:-1] + line
            else:
                paragraphs[-1] = f"{paragraphs[-1]} {line}"
        else:
            paragraphs.append(line)
    return "\n".join(paragraphs)


def preamble(path: str) -> dict[str, str]:
    """Consolidation date, promulgating dahir and latest gazette issue, as printed on the first pages."""
    doc = pymupdf.open(path)
    text = "\n".join(line for page in list(doc)[:4] for line in page_lines(page))
    consolidated = _CONSOLIDATED.search(text)
    dahir = _DAHIR.search(text)
    issues = [int(n) for n in _BO.findall(text)]
    return {
        "consolidated": consolidated.group(1).strip() if consolidated else "",
        "dahir": dahir.group(1).replace("-", ".") if dahir else "",
        "latest_bo": str(max(issues)) if issues else "",
    }


def sort_key(number: str) -> int:
    match = re.match(r"\d+", number)
    return int(match.group()) * 1000 if match else 0


def unique_sequence(articles: list[Article]) -> list[Article]:
    """A number can only appear once in a law; the first run of it is the law's own."""
    seen: set[str] = set()
    out = []
    for article in keep_main_sequence(articles):
        if article.number not in seen and article.text.strip():
            seen.add(article.number)
            out.append(article)
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with open(os.path.join(ROOT, "data", "adala_catalog.json"), encoding="utf-8") as f:
        catalog_rows = json.load(f)
    catalog = {row["id"]: row for row in catalog_rows}
    with open(os.path.join(ROOT, "data", "core_laws.json"), encoding="utf-8") as f:
        laws = json.load(f)

    if os.path.exists(TARGET):
        os.remove(TARGET)
    db = sqlite3.connect(TARGET)
    db.executescript(
        """
        PRAGMA journal_mode=OFF;
        PRAGMA synchronous=OFF;
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE laws (
            slug TEXT PRIMARY KEY, title_ar TEXT, title_fr TEXT, law_number TEXT, domain TEXT, dahir TEXT,
            url_ar TEXT, url_fr TEXT, updated_ar TEXT, updated_fr TEXT,
            consolidated_ar TEXT, consolidated_fr TEXT, latest_bo TEXT,
            count_ar INTEGER, count_fr INTEGER
        );
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY, law TEXT NOT NULL, number TEXT NOT NULL, sort_key INTEGER, lang TEXT NOT NULL,
            kind TEXT, text TEXT NOT NULL, section TEXT, page_from INTEGER, page_to INTEGER
        );
        CREATE INDEX articles_lookup ON articles (law, number, lang);
        CREATE VIRTUAL TABLE articles_fts USING fts5(
            body, heading, content='', tokenize="unicode61 remove_diacritics 0 tokenchars '.-'"
        );
        CREATE VIRTUAL TABLE articles_vocab USING fts5vocab(articles_fts, 'row');
        CREATE TABLE catalog (id INTEGER PRIMARY KEY, name TEXT, lang TEXT, trail TEXT, url TEXT, updated TEXT);
        CREATE VIRTUAL TABLE catalog_fts USING fts5(
            body, content='', tokenize="unicode61 remove_diacritics 0 tokenchars '.-'"
        );
        """
    )

    report: list[dict] = []
    total = 0
    for law in laws:
        row = {k: "" for k in ("url_ar", "url_fr", "updated_ar", "updated_fr", "consolidated_ar", "consolidated_fr", "latest_bo", "dahir")}
        counts = {"ar": 0, "fr": 0}
        entry: dict = {"law": law["slug"]}
        for lang in ("ar", "fr"):
            doc_id = law.get(lang)
            if not doc_id:
                continue
            path = os.path.join(CACHE, f"{doc_id}.pdf")
            info = preamble(path)
            source = catalog[doc_id]
            row[f"url_{lang}"] = source["url"]
            row[f"updated_{lang}"] = source["updated"][:10]
            row[f"consolidated_{lang}"] = info["consolidated"]
            if lang == "ar" or not row["dahir"]:
                row["dahir"] = info["dahir"] or row["dahir"]
            if lang == "ar" or not row["latest_bo"]:
                row["latest_bo"] = info["latest_bo"] or row["latest_bo"]
            raw, chars = split_articles(path)
            kept = unique_sequence(raw)
            cov = coverage(kept)
            counts[lang] = len(kept)
            entry[lang] = {"catalog_id": doc_id, "chars": chars, "articles": len(kept), "first": cov["first"], "last": cov["last"], "missing": cov["missing"], "consolidated": info["consolidated"]}
            for article in kept:
                text = reflow(article.text)
                section = re.sub(r"\s+", " ", article.section)[:300]
                cursor = db.execute(
                    "INSERT INTO articles (law, number, sort_key, lang, kind, text, section, page_from, page_to) VALUES (?,?,?,?,?,?,?,?,?)",
                    (law["slug"], article.number, sort_key(article.number), lang, article.kind, text, section, article.page_from, article.page_to),
                )
                db.execute(
                    "INSERT INTO articles_fts (rowid, body, heading) VALUES (?,?,?)",
                    (cursor.lastrowid, " ".join(stems(text)), " ".join(stems(section))),
                )
                total += 1
        db.execute(
            "INSERT INTO laws VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (law["slug"], law["title_ar"], law["title_fr"], law["law_number"], law["domain"], row["dahir"], row["url_ar"], row["url_fr"], row["updated_ar"], row["updated_fr"], row["consolidated_ar"], row["consolidated_fr"], row["latest_bo"], counts["ar"], counts["fr"]),
        )
        report.append(entry)
        print(f"{law['slug']:24} ar={counts['ar']:5} fr={counts['fr']:5} {row['consolidated_ar'][:24]:24} BO {row['latest_bo']}", flush=True)

    for doc in catalog_rows:
        trail = " › ".join(part.strip() for part in doc["trail"])
        db.execute("INSERT INTO catalog VALUES (?,?,?,?,?,?)", (doc["id"], doc["name"], doc["lang"], trail, doc["url"], doc["updated"][:10]))
        db.execute("INSERT INTO catalog_fts (rowid, body) VALUES (?,?)", (doc["id"], " ".join(stems(f"{doc['name']} {trail}"))))

    built_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    db.executemany(
        "INSERT INTO meta VALUES (?,?)",
        [("built_at", built_at), ("articles", str(total)), ("laws", str(len(laws))), ("catalog_documents", str(len(catalog_rows))), ("source", "https://adala.justice.gov.ma")],
    )
    db.execute("INSERT INTO articles_fts (articles_fts) VALUES ('optimize')")
    db.execute("INSERT INTO catalog_fts (catalog_fts) VALUES ('optimize')")
    db.commit()
    db.execute("VACUUM")
    db.close()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump({"built_at": built_at, "articles": total, "laws": report}, f, ensure_ascii=False, indent=1)
    print(f"{total} articles in {len(laws)} laws; {len(catalog_rows)} catalogue documents; {os.path.getsize(TARGET) // 1024 // 1024} MB")


if __name__ == "__main__":
    main()
