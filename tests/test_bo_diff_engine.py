import unittest
from src.bo_diff_engine import BulletinOfficielDiffEngine
from src.contract_auditor import MoroccanContractAuditor
from server import process_api_request


def test_article_redline_diff_computation():
    old_text = (
        "Article 46: Le capital de la société à responsabilité limitée doit être "
        "de 100.000 dirhams au moins et déposé en banque."
    )
    new_text = (
        "Article 46: Le capital de la société à responsabilité limitée est librement "
        "fixé par les associés dans les statuts sans minimum légal."
    )

    diff = BulletinOfficielDiffEngine.compute_article_redline_diff(
        old_text=old_text,
        new_text=new_text,
        article_ref="Code de Commerce - Article 46 (Loi 24-10 / Loi 19-20)",
        bo_issue="BO n° 6992",
    )

    assert diff["article_ref"] == "Code de Commerce - Article 46 (Loi 24-10 / Loi 19-20)"
    assert diff["bo_issue"] == "BO n° 6992"
    assert len(diff["added_tokens"]) > 0
    assert len(diff["removed_tokens"]) > 0
    assert diff["change_ratio"] > 0.15
    assert diff["compliance_severity"] in ("CRITICAL", "HIGH", "MEDIUM", "LOW")
    assert "<del" in diff["redline_html"]
    assert "<ins" in diff["redline_html"]


def test_builtin_jarida_rasmiya_issues_and_summaries():
    engine = BulletinOfficielDiffEngine()
    issues = engine.list_bo_issues()
    # 4 curated legislative redline reforms + 13 Official Gazette issues from gazette_offline_index.json
    assert len(issues) >= 15

    first_issue = issues[0]
    assert "bo_number" in first_issue
    assert "publication_date" in first_issue
    assert "source_url" in first_issue
    assert "sgg.gov.ma" in first_issue["source_url"]
    assert "amendments" in first_issue
    assert len(first_issue["amendments"]) >= 1

    # Verify trilingual summaries (French, MSA, Moroccan Darija)
    am = first_issue["amendments"][0]
    assert "summary_ar" in am
    assert "summary_fr" in am
    assert "summary_darija" in am
    assert "redline_diff" in am


def test_moroccan_contract_compliance_auditor():
    auditor = MoroccanContractAuditor()
    sample_contract = """
    CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE (CDI)
    Article 1 : La période d'essai pour l'employé est fixée à 12 mois renouvelable deux fois.
    Article 2 : Le salarié renonce par avance à toute indemnité de licenciement abusif.
    Article 3 : Les données biométriques du salarié sont collectées sans déclaration préalable à la CNDP.
    """
    report = auditor.audit_contract(sample_contract, lang="fr")

    assert report["risk_score"] >= 60
    assert len(report["violations"]) >= 2
    cited_codes = " ".join(v["statutory_reference"] for v in report["violations"])
    assert "Code du Travail" in cited_codes
    assert "09-08" in cited_codes


def test_fullstack_api_endpoints():
    import json

    status, health = process_api_request("GET", "/api/health")
    assert status == 200
    assert health["status"] == "ok"
    assert health["bo_issues_count"] >= 15
    assert "Hybrid Okapi BM25" in health["retrieval_engine"]

    status_issues, bo_list = process_api_request("GET", "/api/bo-issues")
    assert status_issues == 200
    assert bo_list["count"] >= 15

    status_q, rag_res = process_api_request(
        "POST",
        "/api/query",
        json.dumps({"query": "Quelles sont les indemnités de licenciement abusif ?", "lang": "fr"}).encode("utf-8"),
    )
    assert status_q == 200
    assert len(rag_res["verbatim_citations"]) >= 1
    assert "rrf_score" in rag_res["verbatim_citations"][0]

    status_diff, diff_res = process_api_request(
        "POST",
        "/api/bo-diff",
        json.dumps(
            {
                "old_text": "Article 10: Le délai est de 30 jours.",
                "new_text": "Article 10: Le délai est réduit à 15 jours ouvrables.",
                "article_ref": "Article 10",
                "bo_issue": "BO n° 7542",
            }
        ).encode("utf-8"),
    )
    assert status_diff == 200
    assert "<del" in diff_res["redline_html"]
    assert "<ins" in diff_res["redline_html"]

    status_audit, audit_res = process_api_request(
        "POST",
        "/api/audit-contract",
        json.dumps(
            {
                "contract_text": "La période d'essai pour l'employé est fixée à 12 mois renouvelable deux fois. Le salarié renonce par avance à toute indemnité de licenciement abusif.",
                "lang": "fr",
            }
        ).encode("utf-8"),
    )
    assert status_audit == 200
    assert audit_res["risk_score"] >= 50
    assert len(audit_res["violations"]) >= 2


def test_gazette_index_entries_never_fabricate_prior_text():
    engine = BulletinOfficielDiffEngine()
    index_amendments = [
        am
        for issue in engine.list_bo_issues()
        for am in issue["amendments"]
        if am.get("provenance") == "gazette_index_summary"
    ]
    assert len(index_amendments) >= 13
    for am in index_amendments:
        # The offline index only holds summaries: no invented "old text", no fake redline.
        assert am["old_text"] is None
        assert am["new_text"] is None
        assert am["redline_diff"] is None
        assert am["summary_fr"] or am["summary_ar"]

    curated = [
        am
        for issue in engine.list_bo_issues()
        for am in issue["amendments"]
        if am.get("provenance") == "curated_paraphrase"
    ]
    assert len(curated) >= 4
    assert all(am["redline_diff"] for am in curated)


class TestBODiffAndContractAuditor(unittest.TestCase):
    def test_all_bo_and_contract_behaviors(self):
        test_article_redline_diff_computation()
        test_builtin_jarida_rasmiya_issues_and_summaries()
        test_gazette_index_entries_never_fabricate_prior_text()
        test_moroccan_contract_compliance_auditor()
        test_fullstack_api_endpoints()


if __name__ == "__main__":
    unittest.main()
