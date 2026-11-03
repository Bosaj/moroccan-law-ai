"""
Answer a legal question with the official text.

The answer is the articles themselves, quoted exactly as cut from the Ministry of Justice's PDFs, each
with its page and a link to the source. The short note above them only says which articles were found
and quotes their closest sentence: it never rephrases the law, so it cannot misstate it.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from .arabic_nlp import MoroccanLegalNLP
from .corpus import Corpus, best_excerpt

DOMAIN_FALLBACK = "general_law"

LEGAL_DISCLAIMERS = {
    "ar": "تنبيه قانوني: هذه النصوص مستخرجة آليا من النسخ الرسمية المنشورة على بوابة عدالة التابعة لوزارة العدل، لأغراض التوجيه. تحقق من الوثيقة الأصلية عبر الرابط، ولا تغني هذه المعلومات عن استشارة محام.",
    "fr": "Avertissement : ces textes sont extraits automatiquement des versions officielles publiées sur le portail Adala du ministère de la Justice, à titre d'orientation. Vérifiez le document d'origine par le lien fourni. Ces informations ne remplacent pas l'avis d'un avocat.",
    "darija": "تنبيه: هاد النصوص مأخوذة أوتوماتيكيا من النسخ الرسمية ديال بوابة عدالة (وزارة العدل) باش تعاونك تلقى القانون. شوف الوثيقة الأصلية من الرابط، وهادشي ما كيعوضش المحامي.",
}

ARTICLE_WORD = {"الفصل": ("الفصل", "Article"), "المادة": ("المادة", "Article")}
_PAGE_SUFFIX = "#page="


def _article_label(kind: str, number: str) -> tuple[str, str]:
    plain = re.sub(r"\s", "", kind or "")
    arabic, french = ARTICLE_WORD.get(plain, ("المادة", "Article"))
    return f"{arabic} {number}", f"{french} {number}"


class MoroccanLegalRAG:
    """Retrieval over the official corpus, shaped for the API and the interface."""

    retrieval_engine = "Official articles: BM25 over stemmed Arabic and French, statutory lexicon for Darija"

    def __init__(self, corpus: Corpus | None = None) -> None:
        self.corpus = corpus or Corpus()

    @property
    def article_count(self) -> int:
        return self.corpus.total_articles

    def citation(self, law_slug: str, number: str, score: float = 0.0) -> Dict[str, Any] | None:
        law = self.corpus.laws[law_slug]
        arabic = self.corpus.article(law_slug, number, "ar")
        french = self.corpus.article(law_slug, number, "fr")
        main = arabic or french
        if main is None:
            return None
        label_ar, label_fr = _article_label(main["kind"], number)
        return {
            "id": f"{law_slug}:{number}",
            "law": law_slug,
            "code": law["title_ar"] if arabic else law["title_fr"],
            "code_ar": law["title_ar"],
            "code_fr": law["title_fr"],
            "law_number": law["law_number"],
            "dahir": law["dahir"],
            "bo_issue": f"BO {law['latest_bo']}" if law["latest_bo"] else "",
            "publication_date": "",
            "article": label_ar,
            "article_fr": label_fr,
            "number": number,
            "topic": (main["section"] or "").split(" · ")[-1],
            "section": main["section"] or "",
            "text_ar": arabic["text"] if arabic else "",
            "text_fr": french["text"] if french else "",
            "page_ar": arabic["page_from"] if arabic else None,
            "page_fr": french["page_from"] if french else None,
            "source_url_ar": f"{law['url_ar']}{_PAGE_SUFFIX}{arabic['page_from']}" if arabic else "",
            "source_url_fr": f"{law['url_fr']}{_PAGE_SUFFIX}{french['page_from']}" if french else "",
            "consolidated_ar": law["consolidated_ar"],
            "consolidated_fr": law["consolidated_fr"],
            "updated_ar": law["updated_ar"],
            "updated_fr": law["updated_fr"],
            "rrf_score": round(score, 4),
        }

    def search_articles(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        hits, _ = self.corpus.search(query, k=limit)
        citations = (self.citation(h.law, h.number, h.score) for h in hits)
        return [c for c in citations if c]

    def verify_citations(self, citations: List[Dict[str, Any]]) -> bool:
        """Every quoted text must match the corpus character for character, and every link its row."""
        if not citations:
            return False
        for citation in citations:
            for lang, field in (("ar", "text_ar"), ("fr", "text_fr")):
                text = citation.get(field)
                if not text:
                    continue
                row = self.corpus.article(citation["law"], citation["number"], lang)
                if row is None or row["text"] != text:
                    return False
        return True

    def verify_references(self, text: str, law_slug: str) -> List[str]:
        """Article numbers mentioned in free text that do not exist in that law. Empty means all exist."""
        numbers = re.findall(r"(?:المادة|الفصل|[Aa]rticle|[Aa]rt\.)\s*(\d+(?:-\d+)*)", text)
        return [n for n in numbers if not self.corpus.exists(law_slug, n)]

    @staticmethod
    def _note(citations: List[Dict[str, Any]], query: str) -> Dict[str, str]:
        if not citations:
            return {
                "ar": "لم نجد نصا قانونيا يطابق سؤالك بما يكفي داخل القوانين المفهرسة. جرب كلمات أخرى، أو ابحث في فهرس الوثائق الرسمية.",
                "fr": "Aucun article suffisamment proche de votre question dans les lois indexées. Essayez d'autres mots, ou cherchez dans le catalogue des documents officiels.",
                "darija": "ما لقيناش فصل قريب بزاف من السؤال ديالك فالقوانين اللي عندنا. جرب بكلمات أخرى، ولا قلب فلائحة الوثائق الرسمية.",
            }
        first = citations[0]
        excerpt_ar = best_excerpt(first["text_ar"], query) if first["text_ar"] else ""
        excerpt_fr = best_excerpt(first["text_fr"], query) if first["text_fr"] else ""
        others_ar = "، ".join(f"{c['article']} من {c['code_ar']}" for c in citations[1:3])
        others_fr = ", ".join(f"{c['article_fr']} ({c['code_fr']})" for c in citations[1:3])
        ar = f"أقرب نص لسؤالك: {first['article']} من {first['code_ar']}."
        fr = f"Texte le plus proche de votre question : {first['article_fr']}, {first['code_fr']}."
        darija = f"أقرب نص للسؤال ديالك: {first['article']} من {first['code_ar']}."
        if excerpt_ar:
            ar += f" جاء فيه: «{excerpt_ar}»"
            darija += f" كيقول: «{excerpt_ar}»"
        if excerpt_fr:
            fr += f" Il dispose : « {excerpt_fr} »"
        elif excerpt_ar:
            fr += " Ce texte n'existe qu'en arabe sur le portail officiel."
        if others_ar:
            ar += f" راجع أيضا: {others_ar}."
            fr += f" Voir aussi : {others_fr}."
            darija += f" شوف حتى: {others_ar}."
        return {"ar": ar, "fr": fr, "darija": darija}

    def answer_query(self, query: str, lang: str = "ar") -> Dict[str, Any]:
        hits, expansion = self.corpus.search(query, k=5)
        citations = [c for c in (self.citation(h.law, h.number, h.score) for h in hits) if c]
        verified = self.verify_citations(citations)

        darija = MoroccanLegalNLP.translate_darija_query(query)
        domain = (self.corpus.laws[citations[0]["law"]]["domain"] if citations else None) or expansion.domain or darija["domain"] or DOMAIN_FALLBACK
        translation = {
            "original_query": query,
            "detected_darija": darija["detected_darija"],
            "domain": domain,
            "expanded_terms": list(dict.fromkeys(expansion.terms))[:8],
            "augmented_query": " ".join([query, *expansion.terms]).strip(),
        }
        note = self._note(citations, query)
        key = lang if lang in LEGAL_DISCLAIMERS else "fr"
        return {
            "query": query,
            "darija_translation": translation,
            "query_translation": translation,
            "domain": domain,
            "detected_domain": domain,
            "retrieval_engine": self.retrieval_engine,
            "matched_articles": citations,
            "verbatim_citations": citations,
            "ai_commentary": note,
            "citation_verified": verified,
            "found": bool(citations),
            "legal_disclaimer": LEGAL_DISCLAIMERS[key],
            "response": note[key],
        }
