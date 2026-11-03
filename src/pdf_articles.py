"""
Turn an official law PDF into its articles, keeping the page each one is on.

Arabic PDFs made in Word store their text in a broken order: "الجلالة" extracts as "الجاللة", "الله" as
"هللا", "المادة" as "ملا ادة". Where each glyph sits on the page tells the truth, though, so lines are
rebuilt from positions, with no dictionary and no guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

EASTERN_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EASTERN = str.maketrans(EASTERN_DIGITS, "0123456789")
MIRRORED = str.maketrans("()", ")(")
LTR_JOINERS = ".-–/:,"
ROW_TOLERANCE = 4.0
ZERO_WIDTH = 0.01
OVERPRINT_GAP = 1.0
FOOTNOTE_RATIO = 0.88
FOOTNOTE_MARKS = "0123456789٠١٢٣٤٥٦٧٨٩()*"
WORD_GAP = 0.11  # of the font size: letters of an Arabic word touch, words do not
MAX_NUMBER_JUMP = 60  # a law's own numbering moves in small steps; a bigger leap is a quoted article

ORDINALS = {
    "الأولى": "1", "الاولى": "1", "الأول": "1", "الثانية": "2", "الثاني": "2", "الثالثة": "3", "الثالث": "3",
    "الرابعة": "4", "الرابع": "4", "الخامسة": "5", "الخامس": "5", "السادسة": "6", "السادس": "6",
    "السابعة": "7", "السابع": "7", "الثامنة": "8", "الثامن": "8", "التاسعة": "9", "التاسع": "9", "العاشرة": "10", "العاشر": "10",
    "premier": "1", "première": "1", "1er": "1", "unique": "unique", "الفريد": "unique", "الفريدة": "unique",
}
_UNITS = {
    "الحادي": 1, "الحادية": 1, "الواحد": 1, "الواحدة": 1, "الثاني": 2, "الثانية": 2, "الثالث": 3, "الثالثة": 3, "الرابع": 4, "الرابعة": 4,
    "الخامس": 5, "الخامسة": 5, "السادس": 6, "السادسة": 6, "السابع": 7, "السابعة": 7, "الثامن": 8, "الثامنة": 8, "التاسع": 9, "التاسعة": 9,
}
_TENS = {
    "العشرون": 20, "العشرين": 20, "الثلاثون": 30, "الثلاثين": 30, "الأربعون": 40, "الأربعين": 40,
    "الخمسون": 50, "الخمسين": 50, "الستون": 60, "الستين": 60, "السبعون": 70, "السبعين": 70,
    "الثمانون": 80, "الثمانين": 80, "التسعون": 90, "التسعين": 90,
}
_UNIT_WORDS = "|".join(_UNITS)
_TEN_WORDS = "|".join(_TENS)
_COMPOUND_ORDINAL = rf"(?:{_UNIT_WORDS})\s+(?:عشر|عشرة)|(?:{_UNIT_WORDS})\s+و\s*(?:{_TEN_WORDS})|{_TEN_WORDS}"
_ORDINAL_WORDS = "|".join(sorted(ORDINALS, key=len, reverse=True))

# A heading is a line that holds nothing but the marker, or the marker and a separator: mentions of
# "المادة 15" inside a sentence must not start a new article.
_NUMBER = rf"(?P<num>[\d٠-٩]+(?:[-–—.][\d٠-٩]+)*(?:er\b|ère\b)?(?:\s*(?:مكرر(?:ة)?|bis|ter|quater)(?:\s*[\d٠-٩]+)?)?|{_COMPOUND_ORDINAL}|{_ORDINAL_WORDS})"
# These PDFs sometimes put a stray space inside a word ("الماد ة23", "ا لمادة48"), so markers allow one.
_MADDA = r"ا\s?ل\s?م\s?ا\s?د\s?ة"
_FASL = r"ا\s?ل\s?ف\s?ص\s?ل"
ARTICLE_LINE = re.compile(rf"^\s*(?P<kind>{_MADDA}|{_FASL}|Article|Art\.)\s*{_NUMBER}\s*(?:[-–—:.]\s*)?(?P<rest>.*)$", re.IGNORECASE)
HEADING_LINE = re.compile(r"^\s*(?:الكتاب|القسم|الباب|الفرع|الجزء|الفصل\s+(?!\s*[\d٠-٩])|Livre\b|Titre\b|Chapitre\b|Section\b|Sous-section\b|LIVRE\b|TITRE\b|CHAPITRE\b)", re.UNICODE)
_ARABIC = re.compile(r"[\u0600-\u06ff]")
# A line ending in a preposition runs on: "... \u0627\u0644\u0641\u0642\u0631\u0629 \u0627\u0644\u0623\u0648\u0644\u0649 \u0645\u0646" / "\u0627\u0644\u0641\u0635\u0644 485."
_OPEN_SENTENCE = re.compile(r"(?:^|\s)(?:\u0645\u0646|\u0641\u064a|\u0625\u0644\u0649|\u0627\u0644\u0649|\u0639\u0644\u0649|\u0639\u0646|\u0648|\u0628\u0645\u0648\u062c\u0628|\u0644\u0623\u062d\u0643\u0627\u0645|de|du|des|\u00e0|et|par|l'article|l\u2019article|aux|au)\s*$", re.IGNORECASE)
_LONE_CLOSING = re.compile(r"(?<=[\u0621-\u064a\d])\((?=\s|$)")
_REFERENCE_END = re.compile(r"[.\u060c\u061b,;]\s*$")
_CLOSED_SENTENCE = re.compile(r"[.:\u061b;\u061f?!]\s*$")
# Words that show a wrapped line of running text, not a heading: "\u0627\u0644\u0645\u0627\u062f\u0629 15 \u0645\u0646 \u0647\u0630\u0627 \u0627\u0644\u0642\u0627\u0646\u0648\u0646"
_CONTINUATION = re.compile(
    r"^(?:\u0645\u0646|\u0623\u0639\u0644\u0627\u0647|\u0627\u0639\u0644\u0627\u0647|\u0623\u062f\u0646\u0627\u0647|\u0627\u062f\u0646\u0627\u0647|\u0648|\u0623\u0648|\u0627\u0648|\u0641\u064a|\u0625\u0644\u0649|\u0627\u0644\u0649|\u0639\u0644\u0649|\u0639\u0646|\u0628\u0639\u062f\u0647|\u0628\u0639\u062f\u0647\u0627|\u0623\u0639\u0644\u0649|\u0627\u0644\u0645\u0630\u0643\u0648\u0631|\u0627\u0644\u0645\u0630\u0643\u0648\u0631\u0629|\u0627\u0644\u0633\u0627\u0628\u0642|\u0627\u0644\u0633\u0627\u0628\u0642\u0629|\u0627\u0644\u062a\u064a|\u0627\u0644\u0630\u064a|\u0648\u0645\u0627|"
    r"[,\u060c\u061b;)]|de\b|du\b|des\b|ci-|et\b|ou\b|\u00e0\b|pr\u00e9cit\u00e9|susvis\u00e9|sus-|alin\u00e9a|ainsi|qui\b)",
    re.IGNORECASE,
)


@dataclass
class Article:
    number: str
    kind: str
    text: str
    page_from: int
    page_to: int
    section: str = ""


def _is_ltr(text: str) -> bool:
    ch = text[0]
    return (ch.isascii() and ch.isalnum()) or "À" <= ch <= "ɏ" or ch in EASTERN_DIGITS


@dataclass
class _Glyph:
    x0: float
    x1: float
    order: int
    text: str
    size: float

    @property
    def center(self) -> float:
        return (self.x0 + self.x1) / 2


def _line_glyphs(line: dict, start: int) -> list[_Glyph]:
    """
    The glyphs of a PDF line. A ligature arrives as zero-width letters followed by one real glyph, and
    its letters read real glyph first, then the zero-width ones backwards.
    """
    glyphs: list[_Glyph] = []
    pending: list[str] = []
    for span in line["spans"]:
        for ch in span["chars"]:
            x0, _, x1, _ = ch["bbox"]
            if x1 - x0 < ZERO_WIDTH:
                pending.append(ch["c"])
                continue
            glyphs.append(_Glyph(x0, x1, start + len(glyphs), ch["c"] + "".join(reversed(pending)), span["size"]))
            pending = []
    # Word breaks its lines mid-ligature too: the last letters then belong to the glyph before them
    if pending and glyphs:
        glyphs[-1].text += "".join(reversed(pending))
    return glyphs


def _drop_overprint(glyphs: list[_Glyph]) -> list[_Glyph]:
    """Fake bold prints each letter twice a hair apart; keep one of each."""
    kept: list[_Glyph] = []
    for glyph in glyphs:
        if kept and glyph.text == kept[-1].text and abs(glyph.center - kept[-1].center) < OVERPRINT_GAP:
            continue
        kept.append(glyph)
    return kept


def _visual_to_logical(glyphs: list[_Glyph]) -> str:
    """
    One row of an Arabic page, read off its glyph positions from right to left.

    The stream order of these PDFs is unreliable and the stored spaces land inside words, but where each
    glyph sits on the page is what the reader sees: a word gap is a real gap. Numbers and Latin words
    still read left to right, so those runs are turned back.
    """
    inked = [g for g in glyphs if not g.text.isspace()]
    ordered = _drop_overprint(sorted(inked, key=lambda g: (-g.center, -g.order)))
    runs: list[str] = []
    i = 0
    while i < len(ordered):
        glyph = ordered[i]
        if i and ordered[i - 1].x0 - glyph.x1 > WORD_GAP * glyph.size:
            runs.append(" ")
        if not _is_ltr(glyph.text):
            runs.append(glyph.text)
            i += 1
            continue
        j = i
        while j + 1 < len(ordered) and ordered[j].x0 - ordered[j + 1].x1 <= WORD_GAP * glyph.size and (
            _is_ltr(ordered[j + 1].text)
            or (ordered[j + 1].text in LTR_JOINERS and j + 2 < len(ordered) and _is_ltr(ordered[j + 2].text))
        ):
            j += 1
        runs.extend(g.text for g in reversed(ordered[i : j + 1]))
        i = j + 1
    text = "".join(runs)
    # Mirrored brackets are stored as drawn: on the right edge of a phrase they read as closing
    first_open, first_close = text.find("("), text.find(")")
    if first_close != -1 and (first_open == -1 or first_close < first_open):
        text = text.translate(MIRRORED)
    # A lone bracket has no partner to judge by: "أ( معالجة" can only be closing a list letter
    text = _LONE_CLOSING.sub(")", text)
    return re.sub(r"\s+", " ", text).strip()


def _body_size(rows: list[tuple[float, list[_Glyph]]]) -> float:
    """The font size most of the page is set in."""
    counts: dict[float, int] = {}
    for _, glyphs in rows:
        for glyph in glyphs:
            size = round(glyph.size, 1)
            counts[size] = counts.get(size, 0) + 1
    return max(counts, key=counts.__getitem__)


def document_body_size(doc: pymupdf.Document) -> float:
    """The font size a whole document is set in: a page of mostly footnotes must not redefine it."""
    counts: dict[float, int] = {}
    for page in doc:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    size = round(span["size"], 1)
                    counts[size] = counts.get(size, 0) + len(span["text"])
    return max(counts, key=counts.__getitem__) if counts else 0.0


def page_lines(page: pymupdf.Page, body_size: float | None = None) -> list[str]:
    """Lines of a page in reading order, rebuilt from where the glyphs sit."""
    pieces: list[tuple[float, list[_Glyph]]] = []
    count = 0
    for block in page.get_text("rawdict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]:
        for line in block.get("lines", []):
            glyphs = _line_glyphs(line, count)
            count += len(glyphs)
            if any(not g.text.isspace() for g in glyphs):
                _, y0, _, y1 = line["bbox"]
                pieces.append(((y0 + y1) / 2, glyphs))
    if not pieces:
        return []
    every = "".join(g.text for _, row in pieces for g in row)
    rtl = len(_ARABIC.findall(every)) > len(every) * 0.3
    pieces.sort(key=lambda r: r[0])
    rows: list[tuple[float, list[_Glyph]]] = []
    for y, glyphs in pieces:
        if rows and abs(rows[-1][0] - y) < ROW_TOLERANCE:
            rows[-1][1].extend(glyphs)
        else:
            rows.append((y, list(glyphs)))
    body = body_size or _body_size(rows)
    height = page.rect.height
    lines = []
    for y, glyphs in rows:
        largest = max(g.size for g in glyphs if not g.text.isspace())
        # Footnotes hold the amendment history, in smaller print at the foot of the page
        if largest < body * FOOTNOTE_RATIO and y > height * 0.4:
            continue
        glyphs = [g for g in glyphs if not (g.size < largest * FOOTNOTE_RATIO and g.text[0] in FOOTNOTE_MARKS)]
        if rtl:
            line = _visual_to_logical(glyphs)
        else:
            ordered = sorted(glyphs, key=lambda g: (g.center, g.order))
            line = re.sub(r"\s+", " ", "".join(g.text for g in ordered)).strip()
        if line:
            lines.append(line)
    return lines


_PAGE_NUMBER = re.compile(r"^[-–—\s]*[\d٠-٩]+[-–—\s]*$")


def _normal_number(raw: str) -> str:
    word = re.sub(r"\s+", " ", raw.strip())
    if word in ORDINALS or word.lower() in ORDINALS:
        return ORDINALS.get(word, ORDINALS.get(word.lower(), word))
    parts = word.replace(" و ", " ").replace(" و", " ").split()
    if parts[0] in _TENS:
        return str(_TENS[parts[0]])
    if parts[0] in _UNITS and len(parts) == 2:
        if parts[1] in _TENS:
            return str(_UNITS[parts[0]] + _TENS[parts[1]])
        return str(_UNITS[parts[0]] + 10)
    word = re.sub(r"(?:er|ère)\b", "", word)
    return word.translate(EASTERN).replace("–", "-").replace("—", "-")


def _kind(marker: str) -> str:
    plain = re.sub(r"\s", "", marker)
    if plain == "الفصل":
        return "fasl"
    if plain == "المادة":
        return "madda"
    return "article"


def _kinds_present(pages: list[list[str]]) -> set[str]:
    kinds: set[str] = set()
    for lines in pages:
        for line in lines:
            match = ARTICLE_LINE.match(line)
            if match and not _CONTINUATION.match(match["rest"]):
                kinds.add(_kind(match["kind"]))
    return kinds


def _split_pages(pages: list[list[str]], main_kind: str | None) -> list[Article]:
    articles: list[Article] = []
    current: Article | None = None
    section = ""
    in_heading = False
    previous = ""
    for page_no, lines in enumerate(pages, start=1):
        for line in lines:
            if _PAGE_NUMBER.match(line):
                continue
            match = ARTICLE_LINE.match(line)
            if match and (
                _CONTINUATION.match(match["rest"])
                or _kind(match["kind"]) != main_kind
                or _OPEN_SENTENCE.search(previous)
                or (_REFERENCE_END.search(line) and not match["rest"] and not _CLOSED_SENTENCE.search(previous))
            ):
                match = None
            previous = line
            if match:
                if current:
                    articles.append(current)
                in_heading = False
                current = Article(_normal_number(match["num"]), match["kind"], match["rest"].strip(), page_no, page_no, section)
            elif HEADING_LINE.match(line):
                # Chapter titles belong to what follows, not to the article before them
                section = line if not in_heading else f"{section} · {line}"
                in_heading = True
            elif in_heading:
                section = f"{section} {line}"
            elif current:
                current.text = f"{current.text}\n{line}".strip()
                current.page_to = page_no
    if current:
        articles.append(current)
    return articles


def split_articles(pdf_path: str) -> tuple[list[Article], int]:
    """
    All articles of a PDF, and how many characters it held (0 means a scan with no text layer).

    A law numbers its own articles one way. When it also quotes another code ("الفصل 404" inside a law
    built on "المادة"), the marker that gives the fuller, gap-free run is the law's own.
    """
    doc = pymupdf.open(pdf_path)
    body_size = document_body_size(doc)
    pages = [page_lines(page, body_size) for page in doc]
    chars = sum(len(line) for lines in pages for line in lines)
    best: list[Article] = []
    best_score = -1.0
    for kind in sorted(_kinds_present(pages)):
        articles = _split_pages(pages, kind)
        kept = keep_main_sequence(articles)
        cov = coverage(kept)
        if cov["first"] is None:
            continue
        span = cov["last"] - cov["first"] + 1
        score = len(kept) * min(1.0, len(kept) / span)
        if score > best_score:
            best, best_score = articles, score
    return best, chars


def _base_number(number: str) -> int | None:
    match = re.match(r"\d+", number)
    return int(match.group()) if match else None


def keep_main_sequence(articles: list[Article]) -> list[Article]:
    """
    Drop headings that break the running order (a law quoted inside another law's preamble, say).
    Keeps the longest non-decreasing run of article numbers, so 1, 2, 3, 3 bis, 4 stays whole.
    """
    numbered = [(i, _base_number(a.number)) for i, a in enumerate(articles)]
    numbered = [(i, n) for i, n in numbered if n is not None]
    if not numbered:
        return articles
    best_len = [1] * len(numbered)
    prev = [-1] * len(numbered)
    for j in range(len(numbered)):
        # looking back a little is enough: real order only breaks locally
        for k in range(max(0, j - 400), j):
            if 0 <= numbered[j][1] - numbered[k][1] <= MAX_NUMBER_JUMP and best_len[k] + 1 > best_len[j]:
                best_len[j] = best_len[k] + 1
                prev[j] = k
    j = max(range(len(numbered)), key=best_len.__getitem__)
    keep: set[int] = set()
    while j >= 0:
        keep.add(numbered[j][0])
        j = prev[j]
    return [a for i, a in enumerate(articles) if i in keep]


def coverage(articles: list[Article]) -> dict[str, object]:
    """How complete the numbering is: gaps are worth a person's look."""
    numbers = sorted({n for a in articles if (n := _base_number(a.number)) is not None})
    if not numbers:
        return {"count": len(articles), "first": None, "last": None, "missing": []}
    missing = sorted(set(range(numbers[0], numbers[-1] + 1)) - set(numbers))
    return {"count": len(articles), "first": numbers[0], "last": numbers[-1], "missing": missing}
