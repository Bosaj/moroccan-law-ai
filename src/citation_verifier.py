"""
Citation-verification layer and evaluation benchmark verifier for Moroccan Law AI (#4).

Verifies that every quoted statutory article matches the official Ministry of Justice (Adala)
corpus character-for-character, validates page-level PDF source anchors, flags hallucinated
article references in free text, and evaluates retrieval accuracy against reviewed gold benchmarks.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List

from .corpus import Corpus

ARTICLE_REF_RE = re.compile(r"(?:المادة|الفصل|[Aa]rticle|[Aa]rt\.)\s*(\d+(?:-\d+)*)")


class CitationVerificationLayer:
    """Cryptographic and structural verification of Moroccan statutory citations."""

    def __init__(self, corpus: Corpus) -> None:
        self.corpus = corpus

    @staticmethod
    def sha256_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def audit_citation(self, citation: Dict[str, Any]) -> Dict[str, Any]:
        law_slug = str(citation.get("law") or "")
        number = str(citation.get("number") or "")
        cid = f"{law_slug}:{number}"

        if law_slug not in self.corpus.laws:
            return {
                "id": cid,
                "verified": False,
                "reason": "unknown_law_slug",
                "sha256_ar": None,
                "sha256_fr": None,
            }

        law_meta = self.corpus.laws[law_slug]
        reasons: List[str] = []
        sha_ar: str | None = None
        sha_fr: str | None = None
        checked_any = False

        for lang, text_key, url_key, page_key, law_url_key in (
            ("ar", "text_ar", "source_url_ar", "page_ar", "url_ar"),
            ("fr", "text_fr", "source_url_fr", "page_fr", "url_fr"),
        ):
            quoted = citation.get(text_key)
            if not quoted:
                continue
            checked_any = True
            row = self.corpus.article(law_slug, number, lang)
            if row is None:
                reasons.append(f"missing_{lang}_article_in_corpus")
                continue
            if row["text"] != quoted:
                reasons.append(f"verbatim_mismatch_{lang}")
            digest = self.sha256_text(row["text"])
            if lang == "ar":
                sha_ar = digest
            else:
                sha_fr = digest

            expected_page = row["page_from"]
            if citation.get(page_key) != expected_page:
                reasons.append(f"page_mismatch_{lang}")
            expected_url = f"{law_meta[law_url_key]}#page={expected_page}"
            if citation.get(url_key) != expected_url:
                reasons.append(f"source_url_mismatch_{lang}")

        if not checked_any:
            reasons.append("empty_citation_text")

        return {
            "id": cid,
            "verified": len(reasons) == 0,
            "reason": "ok" if not reasons else ",".join(reasons),
            "sha256_ar": sha_ar,
            "sha256_fr": sha_fr,
        }

    def audit_response(
        self,
        citations: List[Dict[str, Any]],
        commentary_text: str = "",
    ) -> Dict[str, Any]:
        audits = [self.audit_citation(c) for c in citations]
        verified_count = sum(1 for a in audits if a["verified"])
        unverified_ids = [a["id"] for a in audits if not a["verified"]]

        hallucinated_refs: List[str] = []
        if commentary_text and citations:
            primary_law = str(citations[0].get("law") or "")
            if primary_law in self.corpus.laws:
                mentioned = ARTICLE_REF_RE.findall(commentary_text)
                cited_numbers = {str(c.get("number")) for c in citations}
                for num in mentioned:
                    if num not in cited_numbers and not self.corpus.exists(primary_law, num):
                        hallucinated_refs.append(f"{primary_law}:{num}")

        all_ok = bool(citations) and len(unverified_ids) == 0 and len(hallucinated_refs) == 0
        return {
            "verified": all_ok,
            "total_citations": len(citations),
            "verified_citations": verified_count,
            "unverified_ids": unverified_ids,
            "hallucinated_references": hallucinated_refs,
            "audits": audits,
        }

    @staticmethod
    def evaluate_benchmark_set(
        rag: Any,
        eval_file: str | Path,
        max_cases: int | None = None,
    ) -> Dict[str, Any]:
        path = Path(eval_file)
        items = json.loads(path.read_text(encoding="utf-8"))
        if max_cases is not None:
            items = items[:max_cases]
        total = len(items)
        top1_hits = 0
        top5_hits = 0
        verified_all = 0

        for item in items:
            query = item["q"]
            law = item.get("law", "")
            articles = item.get("articles", [])
            expected = set(item.get("expect", [])) | {f"{law}:{n}" for n in articles}
            res = rag.answer_query(query, lang=item.get("lang", "ar"))
            if res.get("citation_verified"):
                verified_all += 1
            got_ids = [c["id"] for c in res.get("verbatim_citations", [])]
            if got_ids and got_ids[0] in expected:
                top1_hits += 1
            if any(cid in expected for cid in got_ids[:5]):
                top5_hits += 1

        return {
            "benchmark": path.name,
            "total_cases": total,
            "top1_accuracy": round(top1_hits / max(1, total), 4),
            "top5_recall": round(top5_hits / max(1, total), 4),
            "citation_verification_rate": round(verified_all / max(1, total), 4),
        }
