import pytest
from src.arabic_nlp import MoroccanLegalNLP
from src.legal_rag import MoroccanLegalRAG


def test_arabic_normalization():
    text = "الزَّوَاجُ وَالطَّلَاقُ فِي الْمَغْرِبِ"
    normalized = MoroccanLegalNLP.normalize_arabic(text)
    assert "الزواج" in normalized
    assert "الطلاق" in normalized


def test_legal_domain_classification():
    domain_family = MoroccanLegalNLP.classify_legal_domain("ما هي شروط عقد الزواج؟")
    assert domain_family == "family_law"

    domain_labor = MoroccanLegalNLP.classify_legal_domain("طرد تعسفي من العمل بدون إشعار")
    assert domain_labor == "labor_law"


def test_legal_rag_search():
    rag = MoroccanLegalRAG()
    result = rag.answer_query("الطرد التعسفي", lang="ar")
    assert "response" in result
    assert len(result["matched_articles"]) > 0
