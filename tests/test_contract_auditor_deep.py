import unittest
from src.contract_auditor import MoroccanContractAuditor


class TestMoroccanContractAuditorDeep(unittest.TestCase):
    def setUp(self):
        self.auditor = MoroccanContractAuditor()

    def test_compliant_contract_zero_risk(self):
        clean_contract = """
        CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE (CDI)
        Article 1 : L'employé est engagé avec une période d'essai de 15 jours conformément à la loi.
        Article 2 : La rémunération respecte le SMIG légal en vigueur au Maroc.
        Article 3 : Les congés payés sont attribués selon le Code du Travail (Loi 65-99).
        """
        report = self.auditor.audit_contract(clean_contract, lang="fr")
        self.assertEqual(report["status"], "COMPLIANT")
        self.assertEqual(report["risk_score"], 0)
        self.assertEqual(report["violations_count"], 0)
        self.assertEqual(len(report["violations"]), 0)
        self.assertIn("Cet audit automatisé", report["disclaimer"])

    def test_probation_excess_violation_french(self):
        contract = "La période d'essai est fixée à 6 mois renouvelable deux fois."
        report = self.auditor.audit_contract(contract, lang="fr")
        self.assertIn(report["status"], ("REVIEW_REQUIRED", "NON_COMPLIANT_HIGH_RISK"))
        self.assertEqual(report["risk_score"], 35)
        self.assertEqual(report["violations_count"], 1)

        violation = report["violations"][0]
        self.assertEqual(violation["rule_id"], "rule-travail-art-14")
        self.assertEqual(violation["severity"], "HIGH")
        self.assertIn("Article 14", violation["statutory_reference"])
        self.assertIn("Dépassement de la période d'essai", violation["title"])
        self.assertIn("3 mois pour les cadres", violation["remediation"])

    def test_severance_waiver_violation_arabic(self):
        arabic_contract = "يتنازل الأجير مسبقا عن أي تعويض في حالة الفصل من العمل لأي سبب كان."
        report = self.auditor.audit_contract(arabic_contract, lang="ar")
        self.assertEqual(report["risk_score"], 45)
        self.assertEqual(report["violations_count"], 1)

        violation = report["violations"][0]
        self.assertEqual(violation["rule_id"], "rule-travail-art-35-41")
        self.assertEqual(violation["severity"], "CRITICAL")
        self.assertIn("شرط التنازل المسبق", violation["title"])
        self.assertIn("النظام العام", violation["remediation"])
        self.assertIn("⚠️ هذه المراجعة الآلية", report["disclaimer"])

    def test_cndp_privacy_violation(self):
        cndp_contract = "L'entreprise collecte les données biométriques des salariés sans déclaration préalable."
        report = self.auditor.audit_contract(cndp_contract, lang="fr")
        self.assertEqual(report["risk_score"], 30)
        self.assertEqual(report["violations_count"], 1)

        violation = report["violations"][0]
        self.assertEqual(violation["rule_id"], "rule-cndp-loi-09-08")
        self.assertIn("09-08", violation["statutory_reference"])
        self.assertIn("CNDP", violation["remediation"])

    def test_cumulative_high_risk_contract_with_cap(self):
        toxic_contract = """
        Article 1 : Période d'essai de 12 mois renouvelable deux fois.
        Article 2 : Le salarié renonce à toute indemnité de licenciement.
        Article 3 : Données biométriques collectées sans déclaration CNDP.
        """
        report = self.auditor.audit_contract(toxic_contract, lang="fr")
        # 35 + 45 + 30 = 110, capped at 100
        self.assertEqual(report["risk_score"], 100)
        self.assertEqual(report["status"], "NON_COMPLIANT_HIGH_RISK")
        self.assertEqual(report["violations_count"], 3)

    def test_case_insensitivity_and_multiline_matching(self):
        contract = """
        PÉRIODE D'ESSAI :
        UN AN.
        """
        report = self.auditor.audit_contract(contract, lang="fr")
        self.assertEqual(report["violations_count"], 1)
        self.assertEqual(report["violations"][0]["rule_id"], "rule-travail-art-14")

    def test_empty_and_whitespace_contract(self):
        for empty_text in ["", "   \n\t   "]:
            report = self.auditor.audit_contract(empty_text, lang="fr")
            self.assertEqual(report["status"], "COMPLIANT")
            self.assertEqual(report["risk_score"], 0)
            self.assertEqual(report["violations_count"], 0)


if __name__ == "__main__":
    unittest.main()
