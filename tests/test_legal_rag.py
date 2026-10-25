import unittest
from src.arabic_nlp import MoroccanLegalNLP
from src.legal_rag import MoroccanLegalRAG


def test_arabic_normalization():
    text = "الزَّوَاجُ وَالطَّلَاقُ فِي الْمَغْرِبِ"
    normalized = MoroccanLegalNLP.normalize_arabic(text)
    assert "الزواج" in normalized
    assert "الطلاق" in normalized


def test_darija_to_legal_query_translation():
    darija_ar = "جراو عليا من الخدمة بلا سابق إنذار وبغيت نعرف التعويض"
    translated = MoroccanLegalNLP.translate_darija_query(darija_ar)
    assert translated["detected_darija"] is True
    assert translated["domain"] == "labor_law"
    assert len(translated["expanded_terms"]) > 0

    darija_latin = "moul dar bgha ykhrjni mn lkra bla ma y3lemni"
    translated_lat = MoroccanLegalNLP.translate_darija_query(darija_latin)
    assert translated_lat["detected_darija"] is True
    assert translated_lat["domain"] == "real_estate_lease"


def test_legal_domain_classification():
    domain_family = MoroccanLegalNLP.classify_legal_domain("ما هي شروط عقد الزواج؟")
    assert domain_family == "family_law"

    domain_labor = MoroccanLegalNLP.classify_legal_domain("طرد تعسفي من العمل بدون إشعار")
    assert domain_labor == "labor_law"

    domain_privacy = MoroccanLegalNLP.classify_legal_domain("حماية المعطيات الشخصية CNDP 09-08")
    assert domain_privacy == "data_privacy_law"


def test_strict_citation_separation_and_verification():
    rag = MoroccanLegalRAG()
    result = rag.answer_query("الطرد التعسفي وساعات العمل", lang="ar")

    assert "response" in result
    assert "matched_articles" in result
    assert len(result["matched_articles"]) > 0

    # Strict Safety Architecture required by Master Dossier (#07 + #17):
    assert "verbatim_citations" in result
    assert "ai_commentary" in result
    assert "citation_verified" in result
    assert "legal_disclaimer" in result
    assert result["citation_verified"] is True

    first_cit = result["verbatim_citations"][0]
    assert "dahir" in first_cit
    assert "bo_issue" in first_cit
    assert "publication_date" in first_cit
    assert "article" in first_cit
    assert "text_ar" in first_cit
    assert "text_fr" in first_cit


def test_darija_language_response_mode():
    rag = MoroccanLegalRAG()
    result = rag.answer_query("شنو حقوقي إلى طردوني من الخدمة؟", lang="darija")
    assert result["citation_verified"] is True
    assert len(result["ai_commentary"]["darija"]) > 15


class TestMoroccanLegalRAG(unittest.TestCase):
    def test_all_legal_rag_behaviors(self):
        test_arabic_normalization()
        test_darija_to_legal_query_translation()
        test_legal_domain_classification()
        test_strict_citation_separation_and_verification()
        test_darija_language_response_mode()


if __name__ == "__main__":
    unittest.main()
