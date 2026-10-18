"""
Moroccan Law AI - Legal RAG Engine & Knowledge Base
Provides semantic retrieval and article lookup across Moroccan legal codes:
- Moudawana (Code de la Famille)
- Code du Travail (Labor Code)
- Code Pénal (Penal Code)
- Dahir des Obligations et Contrats (DOC)
"""

import json
from typing import Any, Dict, List, Optional
from src.arabic_nlp import MoroccanLegalNLP

# Curated reference database of foundational Moroccan legal articles
MOROCCAN_LEGAL_DATABASE = [
    {
        "code": "Moudawana (مدونة الأسرة)",
        "article": "Article 4",
        "topic": "Marriage Definition",
        "text_ar": "الزواج ميثاق تراض وترابط شرعي بين رجل وامرأة على وجه الدوام، غايته الإحصان والعفاف وإنشاء أسرة مستقرة، برعاية الزوجين.",
        "text_fr": "Le mariage est un pacte fondé sur le consentement mutuel en vue d'établir une union légale et durable entre un homme et une femme.",
        "domain": "family_law",
    },
    {
        "code": "Moudawana (مدونة الأسرة)",
        "article": "Article 49",
        "topic": "Marital Property & Wealth Sharing",
        "text_ar": "لكل واحد من الزوجين ذمة مالية مستقلة عن ذمة الآخر، غير أنه يجوز لهما الاتفاق على استثمار وتوزيع الأموال المكتسبة أثناء قيام الزوجية.",
        "text_fr": "Chacun des deux époux dispose d'un patrimoine propre. Toutefois, ils peuvent convenir d'un cadre pour la gestion des biens acquis pendant le mariage.",
        "domain": "family_law",
    },
    {
        "code": "Code du Travail (مدونة الشغل)",
        "article": "Article 35",
        "topic": "Unfair Dismissal (الطرد التعسفي)",
        "text_ar": "يمنع فصل الأجير دون مبرر مقبول ما لم يكن الفصل مرتبطا بكفاءته أو بسلوكه، وفي حالة الفصل التعسفي يستحق الأجير تعويضا عن الضرر والإشعار.",
        "text_fr": "Il est interdit de licencier un salarié sans motif valable lié à son aptitude ou à sa conduite. Le licenciement abusif ouvre droit à indemnités.",
        "domain": "labor_law",
    },
    {
        "code": "Code du Travail (مدونة الشغل)",
        "article": "Article 184",
        "topic": "Working Hours (ساعات العمل)",
        "text_ar": "تحدد ساعات العمل العادية في النشاطات غير الفلاحية في 2288 ساعة في السنة أو 44 ساعة في الأسبوع.",
        "text_fr": "La durée normale du travail dans les activités non agricoles est fixée à 2288 heures par an ou 44 heures par semaine.",
        "domain": "labor_law",
    },
    {
        "code": "Code Pénal (مجموعة القانون الجنائي)",
        "article": "Article 505",
        "topic": "Theft (جريمة السرقة)",
        "text_ar": "من اختلس عمدا مالا مملوكا للغير يعد سارقا ويعاقب بالحبس من سنة إلى خمس سنوات وغرامة من مائتين إلى خمسمائة درهم.",
        "text_fr": "Quiconque soustrait frauduleusement une chose qui ne lui appartient pas est coupable de vol et puni d'un emprisonnement d'un à cinq ans.",
        "domain": "penal_law",
    },
    {
        "code": "Code Pénal (مجموعة القانون الجنائي)",
        "article": "Article 540",
        "topic": "Fraud & Scamming (جريمة النصب)",
        "text_ar": "يعد مرتكبا لجريمة النصب ويعاقب بالحبس من سنة إلى خمس سنوات وغرامة من خمسمائة إلى خمسة آلاف درهم من استعمل الاحتيال لسلب أموال الغير.",
        "text_fr": "Est coupable d'escroquerie et puni d'un emprisonnement d'un à cinq ans quiconque induit astucieusement en erreur pour se faire remettre des fonds.",
        "domain": "penal_law",
    },
    {
        "code": "Dahir des Obligations et Contrats (قانون الالتزامات والعقود)",
        "article": "Article 77",
        "topic": "Civil Liability & Tort (المسؤولية التقصيرية)",
        "text_ar": "كل فعل ارتكبه الإنسان عن بينة واختيار، ومن غير أن يسمح له به القانون، فأحدث ضررا ماديا أو معنويا للغير، ألزم مرتكبه بتعويض هذا الضرر.",
        "text_fr": "Tout fait quelconque de l'homme qui, sans l'autorité de la loi, cause sciemment et volontairement à autrui un dommage matériel ou moral, oblige son auteur à réparer ledit dommage.",
        "domain": "obligations_contracts",
    },
]


class MoroccanLegalRAG:
    def __init__(self):
        self.db = MOROCCAN_LEGAL_DATABASE

    def search_articles(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        domain = MoroccanLegalNLP.classify_legal_domain(query)
        q_norm = MoroccanLegalNLP.normalize_arabic(query.lower())

        results = []
        for item in self.db:
            score = 0
            if item["domain"] == domain:
                score += 3
            # Text matching
            text_ar_norm = MoroccanLegalNLP.normalize_arabic(item["text_ar"])
            if any(word in text_ar_norm for word in q_norm.split() if len(word) > 2):
                score += 2
            if any(word in item["text_fr"].lower() for word in query.lower().split() if len(word) > 3):
                score += 2

            if score > 0 or domain == "general_law":
                results.append((score, item))

        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:limit]] if results else self.db[:limit]

    def answer_query(self, query: str, lang: str = "ar") -> Dict[str, Any]:
        articles = self.search_articles(query)
        domain = MoroccanLegalNLP.classify_legal_domain(query)

        if lang == "ar":
            intro = f"بناءً على النصوص القانونية المغربية المتعلقة بـ ({domain}):"
            citations = []
            for art in articles:
                citations.append(f"📌 **{art['code']} - {art['article']}** ({art['topic']}):\n> {art['text_ar']}")
            full_response = f"{intro}\n\n" + "\n\n".join(citations)
        else:
            intro = f"Selon les dispositions légales marocaines applicables au domaine ({domain}) :"
            citations = []
            for art in articles:
                citations.append(f"📌 **{art['code']} - {art['article']}** ({art['topic']}):\n> {art['text_fr']}")
            full_response = f"{intro}\n\n" + "\n\n".join(citations)

        return {
            "query": query,
            "domain": domain,
            "matched_articles": articles,
            "response": full_response,
        }
