"""
Turn legal text into search tokens, so a question and an article meet in the same form whichever way
each is written: with or without vowels, alef variants, attached prefixes, French accents or plurals.
"""

from __future__ import annotations

import re
import unicodedata

_DIACRITICS = re.compile(r"[ً-ٰٟـ]")
_EASTERN = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_ARABIC_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه", "ؤ": "و", "ئ": "ي", "ء": "", "ـ": "", "ک": "ك", "ی": "ي", "ڤ": "ف", "گ": "ك"})
_TOKEN = re.compile(r"[0-9a-zء-ي]+(?:[-.][0-9]+)*")
_HAS_ARABIC = re.compile(r"[ء-ي]")

_AR_PREFIXES = ("وبال", "وكال", "وفال", "فبال", "ولل", "فلل", "وال", "فال", "بال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")
_AR_SUFFIXES = ("هما", "كما", "تان", "تين", "ات", "ون", "ين", "ان", "ها", "هم", "هن", "كم", "نا", "يه", "ه", "ي", "ا")
_FR_SUFFIXES = ("issements", "issement", "ations", "ation", "ements", "ement", "ments", "ment", "itions", "ition", "ites", "ite", "euses", "euse", "eurs", "eur", "ees", "ee", "es", "er", "e", "s", "x")

STOPWORDS = frozenset(
    """
    في من على الى عن ان او و ما هذا هذه ذلك تلك التي الذي الذين اللذين اللتين كل اي هو هي هم هن كان كانت يكون تكون
    لا لم لن قد مع بين بعد قبل عند حتى غير له لها لهم به بها فيه فيها منه منها عليه عليها اليه اليها اذا اذ كما لكن
    ثم بل هل ماذا لماذا متى كيف اين كم ايضا انه انها ذات ذو نحو دون حيث لدي عندي انا نحن انت هناك هنا
    ديال ديالي ديالك شنو شنوما واش كيفاش علاش بغيت بغينا ليا عليا ليك عليك دابا شحال فين شكون واخا ماشي هادشي هاد
    داك ديك كاين كاينه راه را غادي غير بلا مع واحد وحده كنت كيدير كندير نقدر تقدر نعرف بغا بغات خاص خاصني
    le la les un une des de du d l et ou a au aux en dans pour par sur que qui quoi quel quelle quels quelles est sont
    ce cet cette ces mon ma mes ton ta tes je j il elle on nous vous ils elles ne n pas plus avec sans se s sa son ses
    leur leurs comment combien pourquoi quand ou peut puis dois doit faire fait etre avoir ai as y c qu si me m moi
    the of to in is are what how when can my i
    chno wach kifach 3lach bghit dyal diali liya 3liya daba ch7al fin chkoun rah bla
    """.split()
)


def normalize(text: str) -> str:
    """Lowercase, no vowel marks, one form of each Arabic letter, no French accents, Western digits."""
    if not text:
        return ""
    text = _DIACRITICS.sub("", text).translate(_EASTERN).translate(_ARABIC_LETTERS).lower()
    decomposed = unicodedata.normalize("NFD", text)
    # Combining marks on Latin letters are accents; Arabic marks are already gone
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn")


def stem(token: str) -> str:
    """Strip the attached particles and endings that make the same word look different."""
    if token.isdigit() or not token:
        return token
    if _HAS_ARABIC.search(token):
        for prefix in _AR_PREFIXES:
            if token.startswith(prefix) and len(token) - len(prefix) >= 3:
                token = token[len(prefix):]
                break
        for suffix in _AR_SUFFIXES:
            if token.endswith(suffix) and len(token) - len(suffix) >= 3:
                return token[: -len(suffix)]
        return token
    if token.endswith("aux") and len(token) > 4:
        return token[:-3] + "al"
    for suffix in _FR_SUFFIXES:
        if token.endswith(suffix) and len(token) - len(suffix) >= 4:
            return token[: -len(suffix)]
    return token


def tokens(text: str) -> list[str]:
    """Normalised words, without the small words that carry no meaning."""
    return [t for t in _TOKEN.findall(normalize(text)) if t not in STOPWORDS and (len(t) > 1 or t.isdigit())]


def stems(text: str) -> list[str]:
    return [stem(t) for t in tokens(text)]


def has_arabic(text: str) -> bool:
    return bool(_HAS_ARABIC.search(normalize(text)))
