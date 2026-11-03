import json
import unittest
from urllib.parse import quote

from server import process_api_request


class TestServerRoutes(unittest.TestCase):
    def test_health_endpoint(self):
        status, payload = process_api_request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload.get("status"), "ok")
        self.assertEqual(payload.get("app"), "moroccan-law-ai")
        self.assertGreater(payload.get("corpus_articles_count", 0), 0)
        self.assertGreater(payload.get("bo_issues_count", 0), 0)

    def test_bo_issues_endpoint(self):
        status, payload = process_api_request("GET", "/api/bo-issues")
        self.assertEqual(status, 200)
        self.assertIn("issues", payload)
        self.assertGreaterEqual(payload["count"], 1)

    def test_bo_issues_filtered_by_audience(self):
        status, payload = process_api_request("GET", "/api/bo-issues?audience=citizens")
        self.assertEqual(status, 200)
        for issue in payload["issues"]:
            audiences_lower = [a.lower() for a in issue["target_audience"]]
            self.assertTrue(any("citizen" in a for a in audiences_lower))

    def test_query_endpoint_invalid_json(self):
        status, payload = process_api_request("POST", "/api/query", b"{not valid json")
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_query_endpoint_valid_question(self):
        body = json.dumps({"query": "délai de préavis licenciement", "lang": "fr"}).encode("utf-8")
        status, payload = process_api_request("POST", "/api/query", body)
        self.assertEqual(status, 200)
        self.assertIn("verbatim_citations", payload)
        self.assertIn("response", payload)
        self.assertIn("matched_articles", payload)
        self.assertGreater(len(payload["verbatim_citations"]), 0)

    def test_bo_diff_endpoint(self):
        body = json.dumps({
            "old_text": "Le délai de préavis est fixé à 8 jours pour tous.",
            "new_text": "Le délai de préavis est fixé à 30 jours pour les cadres.",
            "article_ref": "Article 43",
        }).encode("utf-8")
        status, payload = process_api_request("POST", "/api/bo-diff", body)
        self.assertEqual(status, 200)
        self.assertIn("redline_html", payload)
        self.assertIn("added_tokens", payload)
        self.assertIn("removed_tokens", payload)

    def test_audit_contract_endpoint(self):
        body = json.dumps({
            "contract_text": "La durée de travail est fixée à 60 heures par semaine sans majoration. La période d'essai est de 12 mois.",
            "lang": "fr",
        }).encode("utf-8")
        status, payload = process_api_request("POST", "/api/audit-contract", body)
        self.assertEqual(status, 200)
        self.assertIn("risk_score", payload)
        self.assertIn("violations", payload)
        self.assertGreater(payload["risk_score"], 0)
        self.assertGreater(len(payload["violations"]), 0)

    def test_laws_endpoint_lists_the_corpus(self):
        status, payload = process_api_request("GET", "/api/laws")
        self.assertEqual(status, 200)
        self.assertEqual(payload["count"], len(payload["laws"]))
        labor = next(law for law in payload["laws"] if law["slug"] == "labor")
        self.assertEqual(labor["count_ar"], 589)
        self.assertTrue(labor["url_ar"].startswith("https://adala.justice.gov.ma/"))

    def test_law_endpoint_returns_its_articles(self):
        status, payload = process_api_request("GET", "/api/law?law=commercial-lease&lang=ar")
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["articles"]), 38)
        self.assertTrue(payload["articles"][0]["label"].startswith("المادة"))
        status, _ = process_api_request("GET", "/api/law?law=no-such-law")
        self.assertEqual(status, 404)

    def test_article_endpoint(self):
        status, payload = process_api_request("GET", "/api/article?law=family&number=19")
        self.assertEqual(status, 200)
        self.assertIn("أهلية الزواج", payload["text_ar"])
        status, _ = process_api_request("GET", "/api/article?law=family&number=9999")
        self.assertEqual(status, 404)

    def test_catalog_endpoint(self):
        status, payload = process_api_request("GET", "/api/catalog?q=" + quote("مدونة الشغل"))
        self.assertEqual(status, 200)
        self.assertGreater(payload["count"], 0)
        status, payload = process_api_request("GET", "/api/catalog?q=")
        self.assertEqual(payload["count"], 0)

    def test_empty_question_is_refused(self):
        status, payload = process_api_request("POST", "/api/query", json.dumps({"query": "  "}).encode())
        self.assertEqual(status, 400)
        self.assertIn("error", payload)

    def test_questions_are_not_stored(self):
        secret = "سؤال خاص جدا عن طلاقي"
        process_api_request("POST", "/api/query", json.dumps({"query": secret, "lang": "ar"}).encode())
        from server import _stats_connection

        with _stats_connection() as conn:
            columns = [row[1] for row in conn.execute("PRAGMA table_info(consultation_stats)")]
        self.assertNotIn("query", columns)


if __name__ == "__main__":
    unittest.main()

