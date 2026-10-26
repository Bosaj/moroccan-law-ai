import json
import os
import unittest
from server import (
    PDF_DIR,
    STATIC_DIR,
    get_audit_stats,
    init_db,
    log_consultation,
    log_contract_audit,
    process_api_request,
    resolve_pdf,
    resolve_static,
)


class TestServerSecurityAndApiDeep(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_logging_and_stats(self):
        initial_stats = get_audit_stats()
        initial_consultations = initial_stats["consultations_logged"]
        initial_audits = initial_stats["contract_audits_logged"]

        # Log a consultation
        log_consultation("délai de préavis", "fr", "labor_law", True, 2)
        # Log a contract audit
        log_contract_audit("NON_COMPLIANT_HIGH_RISK", 85, 3)

        new_stats = get_audit_stats()
        self.assertEqual(new_stats["consultations_logged"], initial_consultations + 1)
        self.assertEqual(new_stats["contract_audits_logged"], initial_audits + 1)

    def test_resolve_pdf_path_traversal_guards(self):
        # Valid PDF path within PDF_DIR should resolve
        sample_pdf = os.path.join(PDF_DIR, "ar", "code_famille_moudawana_loi_70_03_ar.pdf")
        if os.path.isfile(sample_pdf):
            resolved = resolve_pdf("/data/laws_pdf/ar/code_famille_moudawana_loi_70_03_ar.pdf")
            self.assertIsNotNone(resolved)
            self.assertEqual(os.path.normpath(resolved), os.path.normpath(sample_pdf))

        # Traversal attacks must all return None
        traversal_attempts = [
            "/data/laws_pdf/../../server.py",
            "/data/laws_pdf/..\\..\\server.py",
            "/data/laws_pdf/%2e%2e/%2e%2e/server.py",
            "/data/laws_pdf/../../../etc/passwd",
            "/data/laws_pdf/C:/Windows/System32/cmd.exe",
            "/server.py",
            "../../data/legal_audit.db",
        ]
        for attempt in traversal_attempts:
            res = resolve_pdf(attempt)
            self.assertIsNone(res, f"Path traversal should have been blocked for: {attempt}")

    def test_resolve_static_path_traversal_and_spa_routing(self):
        index_file = os.path.join(STATIC_DIR, "index.html")
        if os.path.isfile(index_file):
            # Root path resolves to index.html
            self.assertEqual(os.path.normpath(resolve_static("/")), os.path.normpath(index_file))
            # SPA client routes (no extension) resolve to index.html
            self.assertEqual(os.path.normpath(resolve_static("/ask")), os.path.normpath(index_file))
            self.assertEqual(os.path.normpath(resolve_static("/audit")), os.path.normpath(index_file))
            self.assertEqual(os.path.normpath(resolve_static("/gazette")), os.path.normpath(index_file))

        # Traversal attempts must return None
        traversal_attempts = [
            "/../../server.py",
            "/..\\..\\server.py",
            "/../../../etc/shadow",
            "/web/dist/../../server.py",
        ]
        for attempt in traversal_attempts:
            res = resolve_static(attempt)
            self.assertIsNone(res, f"Static traversal should have been blocked for: {attempt}")

    def test_query_api_multilingual_responses(self):
        # 1. French query
        body_fr = json.dumps({"query": "Quel est le délai de préavis pour les cadres ?", "lang": "fr"}).encode("utf-8")
        status, res_fr = process_api_request("POST", "/api/query", body_fr)
        self.assertEqual(status, 200)
        self.assertTrue(res_fr["citation_verified"])
        self.assertIn("response", res_fr)
        self.assertIn("Code du Travail", res_fr["response"])

        # 2. Arabic query
        body_ar = json.dumps({"query": "ما هو أجل الإخطار قبل إنهاء عقد الشغل؟", "lang": "ar"}).encode("utf-8")
        status, res_ar = process_api_request("POST", "/api/query", body_ar)
        self.assertEqual(status, 200)
        self.assertTrue(res_ar["citation_verified"])
        self.assertGreater(len(res_ar["verbatim_citations"]), 0)

        # 3. Darija query
        body_dar = json.dumps({"query": "جراو عليا من الخدمة وبغيت نعرف التعويض ديالي", "lang": "darija"}).encode("utf-8")
        status, res_dar = process_api_request("POST", "/api/query", body_dar)
        self.assertEqual(status, 200)
        self.assertTrue(res_dar["citation_verified"])
        self.assertIn("ai_commentary", res_dar)
        self.assertIn("darija", res_dar["ai_commentary"])

    def test_query_api_malformed_and_empty_inputs(self):
        # Malformed JSON
        status, res = process_api_request("POST", "/api/query", b"{not: valid json}")
        self.assertEqual(status, 400)
        self.assertIn("error", res)

        # Non-dict JSON payload
        status_arr, res_arr = process_api_request("POST", "/api/query", b"[1, 2, 3]")
        self.assertEqual(status_arr, 400)
        self.assertIn("error", res_arr)

        # Empty query string falls back gracefully to default Moroccan labor query
        body_empty = json.dumps({"query": "", "lang": "fr"}).encode("utf-8")
        status, res = process_api_request("POST", "/api/query", body_empty)
        self.assertEqual(status, 200)
        self.assertTrue(res["citation_verified"])
        self.assertGreater(len(res["verbatim_citations"]), 0)

    def test_bo_issues_audience_filtering(self):
        status, res = process_api_request("GET", "/api/bo-issues?audience=citizens")
        self.assertEqual(status, 200)
        for issue in res["issues"]:
            audiences = [a.lower() for a in issue["target_audience"]]
            self.assertTrue(any("citizen" in a for a in audiences))

        # Filtering by non-existent audience should return empty list
        status, res_empty = process_api_request("GET", "/api/bo-issues?audience=nonexistent_category_xyz")
        self.assertEqual(status, 200)
        self.assertEqual(res_empty["count"], 0)
        self.assertEqual(res_empty["issues"], [])

    def test_bo_diff_computation_identical_and_modified(self):
        # Identical texts
        identical_body = json.dumps({
            "old_text": "Article 1 : La société est constituée.",
            "new_text": "Article 1 : La société est constituée.",
            "article_ref": "Article 1",
        }).encode("utf-8")
        status, diff_same = process_api_request("POST", "/api/bo-diff", identical_body)
        self.assertEqual(status, 200)
        self.assertEqual(diff_same["change_ratio"], 0.0)
        self.assertEqual(diff_same["compliance_severity"], "LOW")
        self.assertEqual(len(diff_same["added_tokens"]), 0)
        self.assertEqual(len(diff_same["removed_tokens"]), 0)

        # Completely changed text
        changed_body = json.dumps({
            "old_text": "Le montant du capital est de cinquante mille dirhams.",
            "new_text": "Le montant du capital est librement déterminé par les associés sans minimum légal.",
            "article_ref": "Article 2",
        }).encode("utf-8")
        status, diff_diff = process_api_request("POST", "/api/bo-diff", changed_body)
        self.assertEqual(status, 200)
        self.assertGreater(diff_diff["change_ratio"], 0.3)
        self.assertIn("<del", diff_diff["redline_html"])
        self.assertIn("<ins", diff_diff["redline_html"])

    def test_audit_contract_empty_and_valid(self):
        body_empty = json.dumps({"contract_text": "", "lang": "fr"}).encode("utf-8")
        status, res = process_api_request("POST", "/api/audit-contract", body_empty)
        self.assertEqual(status, 200)
        self.assertEqual(res["status"], "COMPLIANT")
        self.assertEqual(res["risk_score"], 0)

    def test_security_unknown_route(self):
        routes = ["/api/admin", "/api/login", "/api/users", "/api/config", "/api/exec"]
        for r in routes:
            status, res = process_api_request("GET", r)
            self.assertEqual(status, 404)
            self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
