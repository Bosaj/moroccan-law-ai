"""The corpus is the product: these tests hold its text, its search and its citations to account."""

import json
import os
import re

import pytest

from src.corpus import Corpus
from src.legal_rag import MoroccanLegalRAG
from src.legal_text import normalize, stem, stems
from tools.eval_retrieval import GOLD, HELDOUT, OUT_OF_SCOPE, evaluate, gold_problems, load_gold

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def corpus():
    return Corpus()


@pytest.fixture(scope="module")
def rag(corpus):
    return MoroccanLegalRAG(corpus)


# ---- the text itself


@pytest.mark.parametrize("slug,lang,count", [("family", "ar", 400), ("family", "fr", 400), ("labor", "ar", 589), ("civil-procedure", "ar", 644), ("constitution", "ar", 180), ("commercial-lease", "ar", 38)])
def test_whole_laws_are_present(corpus, slug, lang, count):
    assert len(corpus.law_articles(slug, lang)) == count


def test_ligatures_and_word_order_are_repaired(corpus):
    text = "\n".join(row["text"] for row in corpus.law_articles("labor"))
    for broken in ("ملا ادة", "ألجراء", "االنضمام", "الخطار", "ثالثة أشهر", "تمثيال"):
        assert broken not in text, broken
    assert "أجل الإخطار" in text
    assert "ثلاثة أشهر" in text


def test_no_symbol_font_leftovers(corpus):
    rows = corpus.db.execute("SELECT law, number, text FROM articles").fetchall()
    leaking = [(r["law"], r["number"]) for r in rows if re.search("[-�]", r["text"])]
    assert not leaking


def test_footnotes_stay_out_of_articles(corpus):
    # This page of the code is mostly amendment notes, which must not join the article above them
    assert "تمم الفصل" not in normalize(corpus.article("obligations", "3", "ar")["text"]).replace("َ", "")


def test_a_cross_reference_does_not_start_an_article(corpus):
    # "... الفقرة الأولى من / الفصل 486." wraps onto its own line in the penal code
    assert corpus.article("penal", "486", "ar")["text"].startswith("الاغتصاب هو مواقعة")


def test_amending_law_keeps_its_own_numbering(corpus):
    numbers = [row["number"] for row in corpus.law_articles("violence-women")]
    assert numbers[:3] == ["1", "2", "3"]
    assert "404" not in numbers


def test_french_consolidation_date_is_recorded_separately(corpus):
    labor = corpus.laws["labor"]
    assert "2026" in labor["consolidated_ar"]
    assert "2011" in labor["consolidated_fr"]


# ---- search


def test_text_normalisation_meets_in_one_form():
    assert normalize("الزَّوَاجُ") == "الزواج"
    assert normalize("Préavis") == "preavis"
    assert stem(normalize("بالطلاق")) == stem(normalize("الطلاق"))
    assert stems("licenciement abusif") == stems("licenciements abusifs")


def test_named_article_is_returned_alone(corpus):
    hits, _ = corpus.search("المادة 53 من مدونة الأسرة")
    assert [(h.law, h.number) for h in hits] == [("family", "53")]
    hits, _ = corpus.search("article 184 code du travail")
    assert [(h.law, h.number) for h in hits] == [("labor", "184")]


def test_gold_answers_are_supported_by_the_official_text(corpus):
    assert gold_problems(corpus, load_gold(GOLD)) == []
    assert gold_problems(corpus, load_gold(HELDOUT)) == []


def test_retrieval_does_not_regress(corpus):
    stats = evaluate(corpus, load_gold(GOLD))["per_lang"]["all"]
    assert stats["hit5"] / stats["total"] >= 0.90
    stats = evaluate(corpus, load_gold(HELDOUT))["per_lang"]["all"]
    assert stats["hit5"] / stats["total"] >= 0.80


def test_off_topic_questions_are_declined(corpus):
    with open(OUT_OF_SCOPE, encoding="utf-8") as f:
        questions = json.load(f)
    answered = [q for q in questions if corpus.search(q)[0]]
    assert len(answered) <= 1, answered


def test_index_points_only_at_real_articles(corpus):
    with open(os.path.join(ROOT, "data", "legal_index.json"), encoding="utf-8") as f:
        index = json.load(f)
    missing = [ref for entry in index for ref in entry["articles"] if not corpus.exists(*ref.split(":", 1))]
    assert missing == []


def test_lexicon_terms_exist_in_the_statutes(corpus):
    with open(os.path.join(ROOT, "data", "lexicon.json"), encoding="utf-8") as f:
        lexicon = json.load(f)
    terms = {t for entry in lexicon["entries"] for t in entry["terms"]}
    unseen = []
    for term in terms:
        words = stems(term)
        idf = corpus._idf(words)
        if not any(idf[w] > 0 for w in words):
            unseen.append(term)
    assert unseen == []


def test_catalog_finds_official_documents(corpus):
    documents = corpus.search_catalog("الجريمة الإلكترونية") or corpus.search_catalog("مدونة الشغل")
    assert documents
    assert all(d["url"].startswith("https://adala.justice.gov.ma/") for d in documents)


# ---- answers


def test_answer_quotes_official_text_with_its_source(rag):
    answer = rag.answer_query("طردوني من الخدمة بلا سبب", lang="darija")
    assert answer["citation_verified"] is True
    assert answer["found"] is True
    first = answer["verbatim_citations"][0]
    assert first["law"] == "labor"
    assert first["source_url_ar"].startswith("https://adala.justice.gov.ma/")
    assert first["source_url_ar"].endswith(f"#page={first['page_ar']}")
    assert first["text_ar"] in answer["verbatim_citations"][0]["text_ar"]


def test_tampered_quote_fails_verification(rag):
    citations = rag.search_articles("شيك بدون مؤونة")
    assert rag.verify_citations(citations) is True
    forged = [dict(citations[0], text_ar=citations[0]["text_ar"].replace("الشيك", "الكمبيالة", 1) + " زيادة")]
    assert rag.verify_citations(forged) is False


def test_no_match_says_so_and_cites_nothing(rag):
    answer = rag.answer_query("recette de tajine au poulet", lang="fr")
    assert answer["found"] is False
    assert answer["verbatim_citations"] == []
    assert answer["citation_verified"] is False


def test_note_only_quotes_the_law(rag):
    answer = rag.answer_query("شيك بدون مؤونة", lang="ar")
    first = answer["verbatim_citations"][0]
    quoted = re.search(r"«(.+)»", answer["ai_commentary"]["ar"]).group(1).rstrip("…")
    assert quoted in first["text_ar"]


def test_reference_checker_flags_invented_articles(rag):
    assert rag.verify_references("راجع المادة 53", "family") == []
    assert rag.verify_references("راجع المادة 9999", "family") == ["9999"]


def test_contract_rules_cite_articles_that_exist(corpus):
    from src.contract_auditor import MoroccanContractAuditor

    assert corpus.exists("labor", "14")
    assert corpus.exists("labor", "35")
    assert corpus.exists("labor", "41")
    assert corpus.exists("obligations", "109")
    assert corpus.exists("data-protection", "12")
    assert "ثلاثة أشهر" in corpus.article("labor", "14", "ar")["text"]
    assert len(MoroccanContractAuditor.COMPLIANCE_RULES) >= 3
