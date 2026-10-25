"""
Moroccan Contract & Clause Compliance Auditor
Audits employment contracts (CDI/CDD), commercial leases, and service agreements
against mandatory provisions of Moroccan Law (Code du Travail, DOC, Loi 67-12, Loi 09-08 CNDP).
"""

import re
from typing import Any, Dict, List


class MoroccanContractAuditor:
    """Detects non-compliant or high-risk clauses in Moroccan legal contracts."""

    COMPLIANCE_RULES = [
        {
            "id": "rule-travail-art-14",
            "title_fr": "Dépassement de la période d'essai légale en CDI",
            "title_ar": "تجاوز المدة القصوى لفترة الاختبار في عقد الشغل غير محدد المدة",
            "statutory_reference": "Code du Travail (Loi n° 65-99) — Article 14 (BO n° 5167)",
            "severity": "HIGH",
            "risk_points": 35,
            "patterns": [
                r"période d'essai.*(?:6\s*mois|12\s*mois|un\s*an|renouvelable\s*deux\s*fois)",
                r"فترة الاختبار.*(?:ستة أشهر|سنة|تجدد مرتين)",
            ],
            "remediation_fr": "Réduire la période d'essai aux plafonds de l'Article 14 (3 mois pour les cadres, 1.5 mois pour les employés, 15 jours pour les ouvriers, renouvelable une seule fois).",
            "remediation_ar": "تعديل بند فترة الاختبار ليتوافق مع المادة 14 من مدونة الشغل (3 أشهر للأطر، شهر ونصف للمستخدمين، 15 يوماً للعمال، قابلة للتجديد مرة واحدة فقط).",
        },
        {
            "id": "rule-travail-art-35-41",
            "title_fr": "Renonciation anticipée aux indemnités de licenciement (Nullité d'ordre public)",
            "title_ar": "شرط التنازل المسبق عن التعويض عن الفصل التعسفي (باطل بقوة القانون)",
            "statutory_reference": "Code du Travail (Loi n° 65-99) — Articles 35, 41 & DOC Article 109",
            "severity": "CRITICAL",
            "risk_points": 45,
            "patterns": [
                r"renonce.*indemnit[ée].*licenciement",
                r"sans.*aucune.*indemnit[ée].*licenciement",
                r"يتنازل.*مسبقا.*تعويض.*الفصل",
            ],
            "remediation_fr": "Supprimer la clause : les droits et indemnités prévus par le Code du Travail sont d'ordre public ; toute renonciation anticipée est nulle de plein droit.",
            "remediation_ar": "حذف هذا البند فوراً لأن مقتضيات مدونة الشغل المتعلقة بالتعويض عن الفصل من النظام العام ولا يجوز التنازل عنها مسبقاً.",
        },
        {
            "id": "rule-cndp-loi-09-08",
            "title_fr": "Collecte de données personnelles ou biométriques sans autorisation CNDP",
            "title_ar": "جمع المعطيات الشخصية أو البيومترية دون تصريح أو إذن مسبق من لجنة CNDP",
            "statutory_reference": "Loi n° 09-08 relative à la protection des données personnelles — Articles 3, 4 & 12 (BO n° 5714)",
            "severity": "HIGH",
            "risk_points": 30,
            "patterns": [
                r"biom[ée]trique.*sans\s*d[ée]claration",
                r"sans.*cndp",
                r"donn[ée]es\s*personnelles.*sans\s*consentement",
                r"بصمة.*دون\s*ترخيص",
            ],
            "remediation_fr": "Ajouter une clause de consentement explicite et mentionner le numéro de récépissé de déclaration / autorisation préalable auprès de la CNDP conformément à la Loi n° 09-08.",
            "remediation_ar": "إدراج بند الموافقة الصريحة ورقم وصل التصريح أو الإذن المسبق المسلم من اللجنة الوطنية لمراقبة حماية المعطيات ذات الطابع الشخصي (CNDP) طبقاً للقانون 09-08.",
        },
    ]

    def audit_contract(self, contract_text: str, lang: str = "fr") -> Dict[str, Any]:
        violations: List[Dict[str, Any]] = []
        total_risk = 0

        for rule in self.COMPLIANCE_RULES:
            for pat in rule["patterns"]:
                if re.search(pat, contract_text, flags=re.IGNORECASE | re.DOTALL):
                    total_risk += rule["risk_points"]
                    title_str = rule["title_ar"] if lang == "ar" else rule["title_fr"]
                    rem_str = rule["remediation_ar"] if lang == "ar" else rule["remediation_fr"]
                    violations.append(
                        {
                            "rule_id": rule["id"],
                            "title": title_str,
                            "Explanation": title_str,
                            "statutory_reference": rule["statutory_reference"],
                            "severity": rule["severity"],
                            "remediation": rem_str,
                            "Remediation": rem_str,
                        }
                    )
                    break

        risk_score = min(100, total_risk)
        status = (
            "NON_COMPLIANT_HIGH_RISK"
            if risk_score >= 60
            else ("REVIEW_REQUIRED" if risk_score >= 25 else "COMPLIANT")
        )

        return {
            "status": status,
            "risk_score": risk_score,
            "violations_count": len(violations),
            "violations": violations,
            "disclaimer": (
                "⚠️ هذه المراجعة الآلية تستند إلى القواعد الآمرة في التشريع المغربي ولا تعوض المراجعة القانونية لمحامٍ معتمد."
                if lang == "ar"
                else "⚠️ Cet audit automatisé détecte les clauses contraires à l'ordre public marocain à titre indicatif."
            ),
        }
