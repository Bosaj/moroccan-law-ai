import json
import unittest

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

    def test_laws_pdf_endpoint(self):
        status, payload = process_api_request("GET", "/api/laws-pdf")
        self.assertEqual(status, 200)
        self.assertIn("laws", payload)
        self.assertGreaterEqual(payload["total_files_downloaded"], 20)

    def test_pdf_resolution(self):
        from server import resolve_pdf
        pdf_file = resolve_pdf("/data/laws_pdf/ar/code_famille_moudawana_loi_70_03_ar.pdf")
        self.assertIsNotNone(pdf_file)
        self.assertTrue(pdf_file.endswith(".pdf"))

        # Traversal attempts must be blocked
        traversal = resolve_pdf("/data/laws_pdf/../../server.py")
        self.assertIsNone(traversal)

    def test_unknown_route(self):
        status, payload = process_api_request("GET", "/api/nonexistent")
        self.assertEqual(status, 404)
        self.assertIn("error", payload)

    def test_static_resolution(self):
        from server import resolve_static
        root_file = resolve_static("/")
        self.assertIsNotNone(root_file)
        self.assertTrue(root_file.endswith("index.html"))

        # Client-side routing paths should fallback to index.html
        route_file = resolve_static("/ask")
        self.assertIsNotNone(route_file)
        self.assertTrue(route_file.endswith("index.html"))

        # Traversal attempts must be blocked
        traversal = resolve_static("/../../etc/passwd")
        self.assertIsNone(traversal)


if __name__ == "__main__":
    unittest.main()

