"""
Turn an official law PDF into its articles, keeping the page each one is on.

Arabic PDFs made in Word store ligatures in a broken order: "الجلالة" extracts as "الجاللة" and
"الله" as "هللا". The glyphs tell the truth, though: the first letters of a ligature have zero width,
so reversing each zero-width run restores the text exactly, with no dictionary and no guessing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

EASTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
ZERO_WIDTH = 0.01
ROW_TOLERANCE = 4.0

ORDINALS = {
    "الأولى": "1", "الاولى": "1", "الأول": "1", "الثانية": "2", "الثاني": "2", "الثالثة": "3", "الثالث": "3",
    "الرابعة": "4", "الرابع": "4", "الخامسة": "5", "الخامس": "5", "السادسة": "6", "السادس": "6",
    "السابعة": "7", "السابع": "7", "الثامنة": "8", "الثامن": "8", "التاسعة": "9", "التاسع": "9", "العاشرة": "10", "العاشر": "10",
    "premier": "1", "première": "1", "1er": "1", "unique": "unique", "الفريد": "unique", "الفريدة": "unique",
}
_ORDINAL_WORDS = "|".join(sorted(ORDINALS, key=len, reverse=True))

# A heading is a line that holds nothing but the marker, or the marker and a separator: mentions of
# "المادة 15" inside a sentence must not start a new article.
_NUMBER = rf"(?P<num>[\d٠-٩]+(?:[-–—.][\d٠-٩]+)*(?:\s*(?:مكرر(?:ة)?|bis|ter|quater)(?:\s*[\d٠-٩]+)?)?|{_ORDINAL_WORDS})"
# These PDFs sometimes put a stray space inside a word ("الماد ة23", "ا لمادة48"), so markers allow one.
_MADDA = r"ا\s?ل\s?م\s?ا\s?د\s?ة"
_FASL = r"ا\s?ل\s?ف\s?ص\s?ل"
ARTICLE_LINE = re.compile(rf"^\s*(?P<kind>{_MADDA}|{_FASL}|Article|Art\.)\s*{_NUMBER}\s*(?:[-–—:.]\s*)?(?P<rest>.*)$", re.IGNORECASE)
HEADING_LINE = re.compile(r"^\s*(?:الكتاب|القسم|الباب|الفرع|الجزء|الفصل\s+(?!\s*[\d٠-٩])|Livre\b|Titre\b|Chapitre\b|Section\b|Sous-section\b|LIVRE\b|TITRE\b|CHAPITRE\b)", re.UNICODE)
_LEADING_MARKS = re.compile(r"^([.،؛:؟!]+)\s*(.+)$", re.S)
_ARABIC = re.compile(r"[\u0600-\u06ff]")


@dataclass
class Article:
    number: str
    kind: str
    text: str
    page_from: int
    page_to: int
    section: str = ""


def page_lines(page: pymupdf.Page) -> list[str]:
    """Lines of a page in reading order, with ligatures repaired."""
    pieces: list[tuple[float, float, str]] = []
    for block in page.get_text("rawdict", flags=pymupdf.TEXT_PRESERVE_WHITESPACE)["blocks"]:
        for line in block.get("lines", []):
            out: list[str] = []
            for span in line["spans"]:
                run: list[str] = []
                for ch in span["chars"]:
                    x0, _, x1, _ = ch["bbox"]
                    if x1 - x0 < ZERO_WIDTH:
                        run.append(ch["c"])
                    elif run:
                        out.append(ch["c"] + "".join(reversed(run)))
                        run = []
                    else:
                        out.append(ch["c"])
                out.extend(reversed(run))
            text = "".join(out).strip()
            if text:
                x0, y0, _, y1 = line["bbox"]
                pieces.append(((y0 + y1) / 2, x0, text))
    if not pieces:
        return []
    rtl = len(_ARABIC.findall("".join(t for _, _, t in pieces))) > sum(len(t) for _, _, t in pieces) * 0.3
    # Fragments on one baseline are one line, read in the page's direction
    pieces.sort(key=lambda r: r[0])
    rows: list[list[tuple[float, float, str]]] = []
    for piece in pieces:
        if rows and abs(rows[-1][0][0] - piece[0]) < ROW_TOLERANCE:
            rows[-1].append(piece)
        else:
            rows.append([piece])
    lines = []
    for row in rows:
        row.sort(key=lambda r: -r[1] if rtl else r[1])
        line = " ".join(t for _, _, t in row)
        if rtl:
            # Sentence-ending marks are stored at the visual left, which reads as the start
            match = _LEADING_MARKS.match(line)
            if match:
                line = f"{match[2]}{match[1]}"
        lines.append(line)
    return lines


_PAGE_NUMBER = re.compile(r"^[-–—\s]*[\d٠-٩]+[-–—\s]*$")


def _normal_number(raw: str) -> str:
    word = raw.strip()
    if word in ORDINALS or word.lower() in ORDINALS:
        return ORDINALS.get(word, ORDINALS.get(word.lower(), word))
    return re.sub(r"\s+", " ", word.translate(EASTERN)).replace("–", "-").replace("—", "-")


def split_articles(pdf_path: str) -> tuple[list[Article], int]:
    """All articles of a PDF, and how many characters it held (0 means a scan with no text layer)."""
    doc = pymupdf.open(pdf_path)
    articles: list[Article] = []
    current: Article | None = None
    chars = 0
    section = ""
    in_heading = False
    for page_no, page in enumerate(doc, start=1):
        for line in page_lines(page):
            chars += len(line)
            if _PAGE_NUMBER.match(line):
                continue
            match = ARTICLE_LINE.match(line)
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
    return articles, chars


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
            if numbered[k][1] <= numbered[j][1] and best_len[k] + 1 > best_len[j]:
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
