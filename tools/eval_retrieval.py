"""
Measure retrieval against data/eval/gold.json, whose expected articles are checked against the official
text first: an item whose "contains" phrase is not in the expected article is itself reported as wrong.

Run with: python tools/eval_retrieval.py [--failures] [--check-gold]
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.corpus import Corpus  # noqa: E402
from src.legal_text import normalize  # noqa: E402

GOLD = os.path.join(ROOT, "data", "eval", "gold.json")
HELDOUT = os.path.join(ROOT, "data", "eval", "heldout.json")
OUT_OF_SCOPE = os.path.join(ROOT, "data", "eval", "out_of_scope.json")


def load_gold(path: str = GOLD) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def gold_problems(corpus: Corpus, gold: list[dict]) -> list[str]:
    """Gold items that the official text itself does not support."""
    problems = []
    for item in gold:
        texts = []
        for number in item["articles"]:
            for lang in ("ar", "fr"):
                row = corpus.article(item["law"], number, lang)
                if row:
                    texts.append(row["text"])
        if not texts:
            problems.append(f"{item['law']} {item['articles']}: no such article in the corpus ({item['q']})")
        elif item.get("contains") and not any(normalize(item["contains"]) in normalize(t) for t in texts):
            problems.append(f"{item['law']} {item['articles']}: does not contain {item['contains']!r} ({item['q']})")
    return problems


def evaluate(corpus: Corpus, gold: list[dict]) -> dict:
    per_lang: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    failures = []
    for item in gold:
        hits, _ = corpus.search(item["q"], k=5)
        ranked = [(h.law, h.number) for h in hits]
        wanted = {(item["law"], n) for n in item["articles"]}
        rank = next((i for i, key in enumerate(ranked) if key in wanted), None)
        for lang in (item["lang"], "all"):
            stats = per_lang[lang]
            stats["total"] += 1
            if rank is not None:
                stats["hit5"] += 1
                stats["hit3"] += rank < 3
                stats["hit1"] += rank == 0
            stats["law1"] += bool(ranked) and ranked[0][0] == item["law"]
        if rank is None or rank >= 3:
            failures.append((item, ranked, rank))
    return {"per_lang": per_lang, "failures": failures}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    corpus = Corpus()
    failures = []
    for name, path in (("tuning set", GOLD), ("held-out set", HELDOUT)):
        gold = load_gold(path)
        problems = gold_problems(corpus, gold)
        print(f"{name}: {len(gold)} questions; items not supported by the text: {len(problems)}")
        for problem in problems:
            print("  GOLD", problem)
        if "--check-gold" in sys.argv:
            continue
        result = evaluate(corpus, gold)
        failures += result["failures"]
        for lang, s in sorted(result["per_lang"].items()):
            total = s["total"]
            print(f"  {lang:7} n={total:4}  hit@1={s['hit1'] / total:5.1%}  hit@3={s['hit3'] / total:5.1%}  hit@5={s['hit5'] / total:5.1%}  right law first={s['law1'] / total:5.1%}")
    if "--check-gold" in sys.argv:
        return
    if os.path.exists(OUT_OF_SCOPE):
        with open(OUT_OF_SCOPE, encoding="utf-8") as f:
            questions = json.load(f)
        answered = [q for q in questions if corpus.search(q, k=5)[0]]
        print(f"out of scope: {len(questions) - len(answered)}/{len(questions)} correctly declined")
        if "--failures" in sys.argv:
            for q in answered:
                print("  ANSWERED", q)
    if "--failures" in sys.argv:
        for item, ranked, rank in failures:
            print(f"MISS rank={rank} [{item['lang']}] {item['q']}\n     want {item['law']} {item['articles']} got {ranked[:5]}")


if __name__ == "__main__":
    main()
