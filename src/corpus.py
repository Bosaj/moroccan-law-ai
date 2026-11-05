"""
Search over the official articles in data/corpus.sqlite.

A question reaches an article by three routes, merged by rank: its own words, the statutory words a
Darija or lay phrasing maps to (data/lexicon.json), and a direct reference such as "المادة 53 من مدونة
الأسرة". Nothing is ever generated here: every result is a row cut from an official PDF.
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import threading
from dataclasses import dataclass, field

from .legal_text import normalize, stem, stems, tokens

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_PATH = os.path.join(BASE_DIR, "data", "corpus.sqlite")
LEXICON_PATH = os.path.join(BASE_DIR, "data", "lexicon.json")
INDEX_PATH = os.path.join(BASE_DIR, "data", "legal_index.json")

RRF_K = 60
CANDIDATES = 300
EXPANSION_WEIGHT = 0.85
# Below this share of the question's meaningful words, a match is a coincidence, not an answer
MIN_COVERAGE = 0.5
# The opening words of an article usually name its subject ("الإرث انتقال حق ...")
LEAD_WORDS = 14
INDEX_SCORE = 100.0

_REFERENCE = re.compile(
    r"(?:المادة|ماده|مادة|الفصل|فصل|الماده|article|art\.?)\s*(?:رقم\s*|n°\s*)?([\d٠-٩]+(?:[-.][\d٠-٩]+)*(?:\s*(?:مكرر|bis))?)",
    re.IGNORECASE,
)
_EASTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_NOTHING: set[str] = set()
_SENTENCE = re.compile(r"(?<=[.؛;:؟?!])\s+|\n")


@dataclass
class Expansion:
    """What the lexicon understood from a question."""

    terms: list[str] = field(default_factory=list)
    laws: list[str] = field(default_factory=list)
    domain: str | None = None
    triggered: bool = False
    groups: list[set[str]] = field(default_factory=list)
    # Word by word: a question's word, and the statutory words that can stand for it
    alternatives: dict[str, set[str]] = field(default_factory=dict)
    route_laws: list[str] = field(default_factory=list)
    generic_laws: list[str] = field(default_factory=list)


@dataclass
class Hit:
    law: str
    number: str
    score: float
    coverage: float
    direct: bool = False


class Lexicon:
    """Darija, Arabizi and lay wording, mapped to the words the statutes use."""

    def __init__(self, path: str = LEXICON_PATH) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self.entries = [
            {**entry, "_triggers": sorted({normalize(t) for t in entry["triggers"]}, key=len, reverse=True)}
            for entry in raw["entries"]
        ]
        self.law_aliases = {slug: sorted({normalize(a) for a in aliases}, key=len, reverse=True) for slug, aliases in raw["law_aliases"].items()}
        self.words: dict[str, dict] = {}
        self.phrases: list[tuple[str, dict]] = []
        for word in raw.get("words", []):
            mapped = {"to": set(stems(" ".join(word["to"]))), "terms": word["to"], "laws": word.get("laws", [])}
            for form in word["from"]:
                found = stems(form)
                if len(found) == 1:
                    self.words[found[0]] = mapped
                elif found:
                    self.phrases.append((normalize(form), mapped))

    @staticmethod
    def _contains(text: str, phrase: str) -> bool:
        # Whole words only: "vol" must not fire on "volume", nor "عقد" on "معقد"
        return re.search(rf"(?<![0-9a-zء-ي]){re.escape(phrase)}(?![0-9a-zء-ي])", text) is not None

    def expand(self, query: str) -> Expansion:
        text = normalize(query)
        found = Expansion()
        # A particle may be attached in Arabic: "بالطلاق" holds "الطلاق"
        loose = re.sub(r"(?<![0-9a-zء-ي])(?:و|ف|ب|ل|ك)(?=ال)", "", text)
        matched = []
        for entry in self.entries:
            longest = max((len(t) for t in entry["_triggers"] if self._contains(text, t) or self._contains(loose, t)), default=0)
            if longest:
                matched.append((longest, entry))
        # A long phrase says more than a short word: "عقد الشغل" outranks "عقد" in choosing the law
        for _, entry in sorted(matched, key=lambda m: -m[0]):
            found.terms.extend(entry["terms"])
            found.groups.append(set(stems(" ".join(entry["terms"]))))
            # "عقد" or "تعويض" appear in every field of law: they suggest one but cannot choose it
            target = found.generic_laws if entry.get("generic") else found.laws
            for law in entry.get("laws", []):
                if law not in target:
                    target.append(law)
            if entry.get("generic"):
                continue
            found.triggered = True
            found.domain = found.domain or entry.get("domain")
        self._expand_words(text, found)
        found.route_laws.extend(law for law in found.generic_laws if law not in found.route_laws)
        return found

    def _expand_words(self, text: str, found: Expansion) -> None:
        """Everyday words mean a statutory word here. They guide the search but do not vouch for a match."""
        mapped: list[tuple[str, dict]] = [(t, self.words[t]) for t in stems(text) if t in self.words]
        mapped += [(next(iter(stems(p)), p), m) for p, m in self.phrases if self._contains(text, p)]
        for source, word in mapped:
            found.alternatives.setdefault(source, set()).update(word["to"])
            found.terms.extend(word["terms"])
            for law in word["laws"]:
                if law not in found.route_laws:
                    found.route_laws.append(law)

    def mentioned_law(self, query: str) -> str | None:
        text = normalize(query)
        best: tuple[int, str] | None = None
        for slug, aliases in self.law_aliases.items():
            for alias in aliases:
                if self._contains(text, alias) and (best is None or len(alias) > best[0]):
                    best = (len(alias), slug)
        return best[1] if best else None


class LegalIndex:
    """
    The index at the back of a law book: common questions and the articles that answer them, chosen by
    reading the articles. Wording varies, so an entry fires when all its words are in the question.
    """

    def __init__(self, path: str = INDEX_PATH) -> None:
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        self.entries: list[tuple[frozenset[str], list[tuple[str, str]]]] = []
        for entry in raw:
            articles = [tuple(ref.split(":", 1)) for ref in entry["articles"]]
            for phrase in entry["when"]:
                words = frozenset(stems(phrase))
                if words:
                    self.entries.append((words, articles))
        # The more specific phrase answers first
        self.entries.sort(key=lambda e: -len(e[0]))

    def lookup(self, question: set[str]) -> list[tuple[str, str]]:
        found: list[tuple[str, str]] = []
        for words, articles in self.entries:
            if words <= question:
                found.extend(a for a in articles if a not in found)
        return found


class Corpus:
    def __init__(self, path: str = CORPUS_PATH, lexicon: Lexicon | None = None, index: LegalIndex | None = None) -> None:
        self.path = path
        self.lexicon = lexicon or Lexicon()
        self.index = index or LegalIndex()
        self._local = threading.local()
        self.laws = {row["slug"]: dict(row) for row in self.db.execute("SELECT * FROM laws")}
        self.meta = {row["key"]: row["value"] for row in self.db.execute("SELECT key, value FROM meta")}
        self.total_articles = int(self.meta.get("articles", "0"))

    @property
    def db(self) -> sqlite3.Connection:
        """Requests run on several threads at once, and each gets its own read-only connection."""
        connection = getattr(self._local, "connection", None)
        if connection is None:
            connection = sqlite3.connect(f"file:{self.path}?mode=ro&immutable=1", uri=True)
            connection.row_factory = sqlite3.Row
            self._local.connection = connection
        return connection

    # ---- lookups

    def article(self, law: str, number: str, lang: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM articles WHERE law=? AND number=? AND lang=?", (law, number, lang)).fetchone()

    def exists(self, law: str, number: str) -> bool:
        return self.db.execute("SELECT 1 FROM articles WHERE law=? AND number=? LIMIT 1", (law, number)).fetchone() is not None

    def law_articles(self, law: str, lang: str = "ar") -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM articles WHERE law=? AND lang=? ORDER BY id", (law, lang)).fetchall()

    def _fts(self, terms: list[str], law: str | None = None) -> list[tuple[int, str, str, str, str]]:
        if not terms:
            return []
        match = " OR ".join('"' + t.replace('"', "") + '"' for t in terms)
        sql = (
            "SELECT a.id, a.law, a.number, a.text, a.section FROM articles_fts f JOIN articles a ON a.id = f.rowid "
            "WHERE articles_fts MATCH ? " + ("AND a.law = ? " if law else "") + "ORDER BY bm25(articles_fts, 1.0, 3.0) LIMIT ?"
        )
        params = (match, law, CANDIDATES) if law else (match, CANDIDATES)
        return [tuple(row) for row in self.db.execute(sql, params)]

    def _idf(self, terms: list[str]) -> dict[str, float]:
        weights: dict[str, float] = {}
        total = max(self.total_articles, 1)
        for term in terms:
            row = self.db.execute("SELECT doc FROM articles_vocab WHERE term = ?", (term,)).fetchone()
            docs = row[0] if row else 0
            weights[term] = math.log(1 + total / (docs + 1)) if docs else 0.0
        return weights

    # ---- search

    def direct_references(self, query: str, law_hint: str | None) -> list[Hit]:
        hits: list[Hit] = []
        for raw in _REFERENCE.findall(query):
            number = re.sub(r"\s+", " ", raw.translate(_EASTERN)).strip().replace("مكرر", "").strip() or raw
            candidates = [law_hint] if law_hint else []
            for law in candidates:
                if law and self.exists(law, number):
                    hits.append(Hit(law, number, 1000.0, 1.0, direct=True))
        return hits

    def search(self, query: str, k: int = 5, law: str | None = None) -> tuple[list[Hit], Expansion]:
        expansion = self.lexicon.expand(query)
        mentioned = law or self.lexicon.mentioned_law(query)
        direct = self.direct_references(query, mentioned or (expansion.laws[0] if expansion.laws else None))
        # Someone who names an article wants that article
        if direct:
            return direct[:k], expansion

        question = list(dict.fromkeys(stems(_REFERENCE.sub(" ", query))))
        extra = [t for t in dict.fromkeys(stems(" ".join(expansion.terms))) if t not in question]
        idf = self._idf(question + extra)
        known = [t for t in question if idf.get(t, 0) > 0]
        # A word the corpus has never seen still counts against coverage: "tajine" is why a recipe is no law
        unseen_weight = math.log(1 + max(self.total_articles, 1))
        weight_all = sum(idf.get(t) or unseen_weight for t in question) or 1.0

        scores: dict[tuple[str, str], float] = {}
        rows: dict[tuple[str, str], list[tuple[str, str]]] = {}
        for weight, terms in ((1.0, known), (EXPANSION_WEIGHT, extra)):
            for rank, (_, law_slug, number, text, section) in enumerate(self._fts(terms, law)):
                key = (law_slug, number)
                scores[key] = scores.get(key, 0.0) + weight / (RRF_K + rank)
                rows.setdefault(key, [])
                if (text, section) not in rows[key]:
                    rows[key].append((text, section))

        hits: list[Hit] = []
        for key, base in scores.items():
            coverage = lead = 0.0
            adjacent = groups = extras = 0
            # An article may be held in two languages: the better match speaks for it
            for text, section in rows[key]:
                words = stems(text)
                present = set(words) | set(stems(section))
                coverage = max(coverage, sum(idf.get(t) or unseen_weight for t in question if t in present or expansion.alternatives.get(t, _NOTHING) & present) / weight_all)
                opening = set(words[:LEAD_WORDS])
                lead = max(lead, sum(idf.get(t, 0) for t in question if t in opening) / weight_all)
                pairs = set(zip(words, words[1:]))
                adjacent = max(adjacent, sum(1 for pair in zip(question, question[1:]) if pair in pairs))
                extras = max(extras, sum(1 for t in extra if t in opening))
                groups = max(groups, sum(1 for group in expansion.groups if group & present))
            score = base * 40 + coverage * 1.5 + lead * 2.0 + min(adjacent, 3) * 0.5 + min(extras, 4) * 0.15 + groups * 0.5
            if key[0] == mentioned:
                score += 3.0
            elif key[0] in expansion.laws:
                score += 1.5 - 0.3 * expansion.laws.index(key[0])
            elif key[0] in expansion.route_laws:
                score += 1.2 - 0.2 * expansion.route_laws.index(key[0])
            elif expansion.laws:
                score *= 0.6
            elif expansion.route_laws:
                score *= 0.75
            hits.append(Hit(key[0], key[1], score, coverage))
        hits.sort(key=lambda h: h.score, reverse=True)

        strong = [h for h in hits if h.coverage >= MIN_COVERAGE or h.law == mentioned or (expansion.triggered and h.law in expansion.laws)]
        pinned = [
            Hit(law_slug, number, INDEX_SCORE - i * 0.1, 1.0)
            for i, (law_slug, number) in enumerate(self.index.lookup(set(question).union(*expansion.alternatives.values())))
            if (not mentioned or law_slug == mentioned) and (not law or law_slug == law) and self.exists(law_slug, number)
        ]
        seen = {(h.law, h.number) for h in pinned}
        return (pinned + [h for h in strong if (h.law, h.number) not in seen])[:k], expansion

    def search_catalog(self, query: str, lang: str | None = None, limit: int = 20) -> list[dict]:
        terms = list(dict.fromkeys(stems(query)))
        if not terms:
            return []
        match = " AND ".join('"' + t.replace('"', "") + '"' for t in terms)
        sql = "SELECT c.* FROM catalog_fts f JOIN catalog c ON c.id = f.rowid WHERE catalog_fts MATCH ? " + ("AND c.lang = ? " if lang else "") + "ORDER BY bm25(catalog_fts) LIMIT ?"
        params = (match, lang, limit) if lang else (match, limit)
        return [dict(row) for row in self.db.execute(sql, params)]


def best_excerpt(text: str, query: str, limit: int = 320) -> str:
    """The sentence of an article closest to the question, for the summary line. Always verbatim."""
    wanted = {stem(t) for t in tokens(query)}
    sentences = [s.strip() for s in _SENTENCE.split(text) if s.strip()]
    if not sentences:
        return text[:limit]
    best = max(sentences, key=lambda s: len(wanted & set(stems(s))))
    return best if len(best) <= limit else best[:limit].rsplit(" ", 1)[0] + "…"
