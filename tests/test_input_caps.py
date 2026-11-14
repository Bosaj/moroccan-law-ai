"""Anonymous endpoints must not let one request use the whole function time budget."""

import json
import time
import unittest

from server import MAX_CONTRACT_CHARS, MAX_DIFF_TEXT_CHARS, init_db, process_api_request
from src.contract_auditor import MoroccanContractAuditor


def _post(route, payload):
    return process_api_request("POST", route, json.dumps(payload).encode("utf-8"))


class TestInputCaps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_contract_longer_than_cap_is_refused(self):
        status, _ = _post("/api/audit-contract", {"contract_text": "a" * (MAX_CONTRACT_CHARS + 1)})
        self.assertEqual(status, 400)

    def test_diff_text_longer_than_cap_is_refused(self):
        status, _ = _post("/api/bo-diff", {"old_text": "a " * MAX_DIFF_TEXT_CHARS, "new_text": "b"})
        self.assertEqual(status, 400)

    def test_crafted_contract_at_the_cap_is_fast(self):
        # Many start words and no final word: the old unbounded ".*" patterns
        # backtracked cubically (8,000 characters took about 4 seconds).
        text = ("sans aucune " * (MAX_CONTRACT_CHARS // 12))[:MAX_CONTRACT_CHARS]
        started = time.perf_counter()
        status, _ = _post("/api/audit-contract", {"contract_text": text})
        self.assertEqual(status, 200)
        self.assertLess(time.perf_counter() - started, 3.0)

    def test_bounded_patterns_still_detect_the_clause(self):
        report = MoroccanContractAuditor().audit_contract(
            "Le salarié renonce par avance à toute indemnité de licenciement."
        )
        self.assertIn("rule-travail-art-35-41", [v["rule_id"] for v in report["violations"]])


if __name__ == "__main__":
    unittest.main()
