"""
Moroccan Law AI - Arabic, French & Moroccan Darija Legal NLP Processor
Handles text normalization, diacritic removal, Darija-to-MSA/French legal translation,
and statutory domain classification across Moroccan Legal Codes:
- Moudawana (Code de la Famille - Loi 70-03)
- Code du Travail (Loi 65-99)
- Code Pénal (Dahir 1-59-413)
- Dahir des Obligations et Contrats (DOC)
- Code de Commerce (Loi 15-95 / Loi 19-20)
- Baux d'Habitation et Professionnels (Loi 67-12)
- Protection des Données Personnelles (Loi 09-08 CNDP)
"""

import re
from typing import Any, Dict, List


class MoroccanLegalNLP:
    ARABIC_DIACRITICS = re.compile(r"[\u064B-\u065F\u0670]")
    ARABIC_TATWEEL = re.compile(r"\u0640")

    LEGAL_TOPICS: Dict[str, List[str]] = {
        "family_law": [
            "زواج", "طلاق", "نفقة", "حضانة", "إرث", "تركة", "شقاق", "مدونة الأسرة",
            "mariage", "divorce", "moudawana", "heritage", "pension alimentaire", "garde",
            "zwaj", "tla9", "tlaq", "nafa9a", "hadana", "irth",
        ],
        "labor_law": [
            "أجر", "عقد عمل", "طرد تعسفي", "عطلة", "أجير", "مشغل", "ساعات العمل", "مدونة الشغل", "تعويض عن الفصل",
            "salaire", "contrat de travail", "licenciement", "preavis", "conge", "smig", "cnss", "periode d'essai",
            "jraw 3liya", "جراو عليا", "طردوني", "الخدمة", "lkhdma", "patron", "chomage", "سابق إنذار",
        ],
        "penal_law": [
            "سرقة", "نصب", "احتيال", "عقوبة", "حبس", "غرامة", "خيانة الأمانة", "تزوير", "جريمة",
            "vol", "escroquerie", "peine", "amende", "infraction", "abus de confiance",
            "chffar", "nsb", "نصبو عليا",
        ],
        "commercial_law": [
            "شركة", "سجل تجاري", "كمبيالة", "شيك", "شيك بدون رصيد", "إفلاس", "صعوبات المقاولة", "مدونة التجارة",
            "societe", "sarl", "registre du commerce", "cheque", "faillite", "fonds de commerce",
            "chèque sans provision", "شيك خاوي", "شركة ذات مسؤولية محدودة",
        ],
        "obligations_contracts": [
            "التزام", "عقد", "مسؤولية مدنية", "مسؤولية تقصيرية", "تعويض", "فسخ العقد", "شرط جزائي",
            "contrat", "responsabilite civile", "dommages", "doc", "obligation", "resiliation",
        ],
        "real_estate_lease": [
            "كراء", "إفراغ", "السومة الكرائية", "المكري", "المكتري", "عقد الكراء", "تحفيظ عقاري",
            "loyer", "bail", "expulsion", "locataire", "proprietaire", "conservation fonciere",
            "moul dar", "مول الدار", "lkra", "الكرا", "يخرجني من الدار", "ykhrjni",
        ],
        "data_privacy_law": [
            "حماية المعطيات الشخصية", "معطيات ذات طابع شخصي", "كاميرات المراقبة", "بصمة", "09-08",
            "cndp", "donnees personnelles", "biometrique", "rgpd", "vie privee", "loi 09-08",
        ],
    }

    DARIJA_LEXICON_MAP: List[Dict[str, Any]] = [
        {
            "patterns": ["جراو عليا", "طردوني", "خرجوني من الخدمة", "jraw 3liya", "tardouni", "lkhdma"],
            "domain": "labor_law",
            "msa_terms": ["طرد تعسفي", "فصل الأجير", "التعويض عن الضرر والإشعار", "مدونة الشغل المادة 35 و 41"],
            "fr_terms": ["licenciement abusif", "indemnité de licenciement", "préavis", "Code du Travail Art. 35 & 41"],
        },
        {
            "patterns": ["مول الدار", "بغا يخرجني", "الكرا", "moul dar", "ykhrjni", "lkra"],
            "domain": "real_estate_lease",
            "msa_terms": ["إنهاء عقد الكراء", "دعوى الإفراغ", "الإشعار بالإفراغ", "القانون 67.12"],
            "fr_terms": ["congé de bail", "procédure d'expulsion", "Loi 67-12 baux d'habitation"],
        },
        {
            "patterns": ["شيك بدون رصيد", "شيك خاوي", "cheque bla rssid", "cheque sans provision"],
            "domain": "commercial_law",
            "msa_terms": ["إصدار شيك بدون مؤونة", "مدونة التجارة المادة 316"],
            "fr_terms": ["émission de chèque sans provision", "Code de Commerce Article 316"],
        },
        {
            "patterns": ["النفقة", "الحضانة", "الطلاق", "tla9", "nafa9a", "hadana", "شقاق"],
            "domain": "family_law",
            "msa_terms": ["تطليق الشقاق", "النفقة والحضانة", "مدونة الأسرة"],
            "fr_terms": ["divorce pour discorde (chiqaq)", "pension alimentaire et garde", "Moudawana"],
        },
        {
            "patterns": ["نصبو عليا", "الاحتيال", "nsbou 3liya", "khdaw liya floussi"],
            "domain": "penal_law",
            "msa_terms": ["جريمة النصب والاحتيال", "القانون الجنائي الفصل 540"],
            "fr_terms": ["escroquerie", "Code Pénal Article 540"],
        },
    ]

    @classmethod
    def normalize_arabic(cls, text: str) -> str:
        if not text:
            return ""
        text = cls.ARABIC_DIACRITICS.sub("", text)
        text = cls.ARABIC_TATWEEL.sub("", text)
        text = re.sub(r"[إأآا]", "ا", text)
        text = re.sub(r"ى", "ي", text)
        text = re.sub(r"ة", "ه", text)
        return text.strip()

    @classmethod
    def translate_darija_query(cls, query: str) -> Dict[str, Any]:
        """
        Detects Moroccan Darija expressions (Arabic script or Latin Arabizi)
        and expands them into formal MSA & French legal search terms.
        """
        q_lower = query.lower()
        q_norm = cls.normalize_arabic(q_lower)

        expanded_terms: List[str] = []
        matched_domain = None
        detected_darija = False

        for entry in cls.DARIJA_LEXICON_MAP:
            for pat in entry["patterns"]:
                pat_norm = cls.normalize_arabic(pat.lower())
                if pat_norm in q_norm or pat.lower() in q_lower:
                    detected_darija = True
                    matched_domain = entry["domain"]
                    expanded_terms.extend(entry["msa_terms"])
                    expanded_terms.extend(entry["fr_terms"])
                    break

        # Also check conversational Darija particles ("شنو", "واش", "بغيت", "كيفاش", "علاش", "ديال")
        darija_particles = ["شنو", "واش", "بغيت", "كيفاش", "علاش", "ديال", "بلا", "3liya", "bghit", "wach", "chno"]
        if any(p in q_lower or cls.normalize_arabic(p) in q_norm for p in darija_particles):
            detected_darija = True

        domain = matched_domain or cls.classify_legal_domain(query)
        return {
            "original_query": query,
            "detected_darija": detected_darija,
            "domain": domain,
            "expanded_terms": list(dict.fromkeys(expanded_terms)),
            "augmented_query": f"{query} {' '.join(expanded_terms)}".strip(),
        }

    @classmethod
    def classify_legal_domain(cls, query: str) -> str:
        q_lower = query.lower()
        q_norm = cls.normalize_arabic(q_lower)

        best_domain = "general_law"
        best_hits = 0

        for domain, keywords in cls.LEGAL_TOPICS.items():
            hits = 0
            for kw in keywords:
                kw_norm = cls.normalize_arabic(kw.lower())
                if kw_norm in q_norm or kw.lower() in q_lower:
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_domain = domain

        return best_domain
