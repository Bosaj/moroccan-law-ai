"""
Moroccan Law AI - Arabic & French Legal NLP Processor
Handles text normalization, diacritic removal, and legal term extraction
for Moroccan Legal Codes (Moudawana, Code Penal, Code du Travail, DOC).
"""

import re
import unicodedata
from typing import Dict, List, Optional


class MoroccanLegalNLP:
    ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
    ARABIC_TATWEEL = re.compile(r"\u0640")

    LEGAL_TOPICS = {
        "family_law": ["زواج", "طلاق", "نفقة", "حضانة", "إرث", "تركة", "mariage", "divorce", "moudawana", "heritage"],
        "labor_law": ["أجر", "عقد عمل", "طرد تعسفي", "عطلة", "salaire", "contrat de travail", "licenciement", "preavis"],
        "penal_law": ["سرقة", "نصب", "احتيال", "عقوبة", "حبس", "غرامة", "vol", "escroquerie", "peine", "amende", "infraction"],
        "commercial_law": ["شركة", "سجل تجاري", "كمبيالة", "شيك", "societe", "registre du commerce", "cheque", "faillite"],
        "obligations_contracts": ["التزام", "عقد", "مسؤولية مدنية", "تعويض", "contrat", "responsabilite civile", "dommages"],
    }

    @classmethod
    def normalize_arabic(cls, text: str) -> str:
        if not text:
            return ""
        # Remove diacritics and tatweel
        text = cls.ARABIC_DIACRITICS.sub("", text)
        text = cls.ARABIC_TATWEEL.sub("", text)
        # Normalize alefs
        text = re.sub(r"[إأآا]", "ا", text)
        # Normalize yaa and taa marbuta
        text = re.sub(r"ى", "ي", text)
        text = re.sub(r"ة", "ه", text)
        return text.strip()

    @classmethod
    def classify_legal_domain(cls, query: str) -> str:
        q_norm = cls.normalize_arabic(query.lower())
        for domain, keywords in cls.LEGAL_TOPICS.items():
            for kw in keywords:
                if kw in q_norm or kw in query.lower():
                    return domain
        return "general_law"
