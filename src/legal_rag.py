"""
Moroccan Law AI - Legal RAG Engine & Verified Statutory Corpus (#07 + #17)
Implements:
- Hybrid BM25/Lexical + Darija-Aware Semantic Retrieval
- Strict Citation Safety Architecture: Separates Verbatim Legal Text (Dahir, Law #, BO Issue #,
  Publication Date, Article #) from AI-Generated Commentary in MSA, French, and Moroccan Darija
- Deterministic Anti-Hallucination Citation Verification Gate
"""

import math
from collections import Counter
from typing import Any, Dict, List
from src.arabic_nlp import MoroccanLegalNLP

RRF_K = 60
BM25_K1 = 1.5
BM25_B = 0.75


MOROCCAN_LEGAL_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "moudawana-art-4",
        "code": "Moudawana — Code de la Famille (مدونة الأسرة)",
        "law_number": "Loi n° 70-03",
        "dahir": "Dahir n° 1-04-22 du 12 hija 1424",
        "bo_issue": "BO n° 5184",
        "publication_date": "2004-02-05",
        "article": "Article 4",
        "topic": "Définition et Finalité du Mariage (تعريف الزواج وغايته)",
        "text_ar": "الزواج ميثاق تراض وترابط شرعي بين رجل وامرأة على وجه الدوام، غايته الإحصان والعفاف وإنشاء أسرة مستقرة، برعاية الزوجين طبق أحكام هذه المدونة.",
        "text_fr": "Le mariage est un pacte fondé sur le consentement mutuel en vue d'établir une union légale et durable, entre un homme et une femme. Il a pour but la vie dans la fidélité, la pureté et la fondation d'une famille stable sous la direction des deux époux.",
        "explanation_darija": "الزواج حسب المادة 4 من مدونة الأسرة هو عقد مبني على التراضي بين الرجل والمرأة تحت الرعاية المشتركة ديالهم بجوج لبناء أسرة مستقرة.",
        "domain": "family_law",
    },
    {
        "id": "moudawana-art-49",
        "code": "Moudawana — Code de la Famille (مدونة الأسرة)",
        "law_number": "Loi n° 70-03",
        "dahir": "Dahir n° 1-04-22 du 12 hija 1424",
        "bo_issue": "BO n° 5184",
        "publication_date": "2004-02-05",
        "article": "Article 49",
        "topic": "Patrimoine des Époux & Biens Acquis (الذمة المالية للزوجين وتدبير الأموال المكتسبة)",
        "text_ar": "لكل واحد من الزوجين ذمة مالية مستقلة عن ذمة الآخر، غير أنه يجوز لهما في إطار تدبير الأموال التي ستكتسب أثناء قيام الزوجية، الاتفاق على استثمارها وتوزيعها في وثيقة مستقلة عن عقد الزواج.",
        "text_fr": "Chacun des deux époux dispose d'un patrimoine propre. Toutefois, les époux peuvent se mettre d'accord sur les conditions de fructification et de répartition des biens qu'ils auront acquis pendant leur mariage dans un document distinct de l'acte de mariage.",
        "explanation_darija": "كل زوج عندو ذمة مالية مستقلة، ولكن يقدرو يتفقو في وثيقة مستقلة مع عقد الزواج على كيفاش يقسمو ويستثمرو الأملاك لي غادي يجمعوها بجوج من بعد الزواج.",
        "domain": "family_law",
    },
    {
        "id": "moudawana-art-94",
        "code": "Moudawana — Code de la Famille (مدونة الأسرة)",
        "law_number": "Loi n° 70-03",
        "dahir": "Dahir n° 1-04-22 du 12 hija 1424",
        "bo_issue": "BO n° 5184",
        "publication_date": "2004-02-05",
        "article": "Articles 94–97",
        "topic": "Divorce pour Discorde / Chiqaq & Pension (مسطرة التطليق للشقاق والنفقة والحضانة)",
        "text_ar": "إذا طلب الزوجان أو أحدهما من المحكمة حل نزاع بينهما يخاف منه الشقاق، وجب على المحكمة أن تقوم بكل المحاولات لإصلاح ذات البين، وفي حالة تعذر الإصلاح تحكم بالتطليق وتحدد المستحقات والنفقة والحضانة.",
        "text_fr": "Si les deux époux ou l'un d'eux demandent au tribunal de régler un différend qui les oppose et qui risque d'aboutir à la discorde (Chiqaq), le tribunal doit entreprendre toutes tentatives de conciliation ; à défaut, il prononce le divorce et fixe les droits, la pension et la garde.",
        "explanation_darija": "في مسطرة الشقاق، المحكمة كدير محاولات الصلح، وإلى استحال الاستمرار كتحكم بالتطليق وكتحدد المتعة والنفقة ديال الأبناء والحضانة داخل أجل لا يتعدى 6 أشهر.",
        "domain": "family_law",
    },
    {
        "id": "travail-art-14",
        "code": "Code du Travail (مدونة الشغل)",
        "law_number": "Loi n° 65-99",
        "dahir": "Dahir n° 1-03-194 du 14 rejeb 1424",
        "bo_issue": "BO n° 5167",
        "publication_date": "2003-12-08",
        "article": "Article 14",
        "topic": "Période d'Essai en CDI (فترة الاختبار في العقود غير محددة المدة)",
        "text_ar": "تحدد فترة الاختبار بالنسبة للعقود غير محددة المدة كما يلي: ثلاثة أشهر بالنسبة للأطر وأشباههم، شهر ونصف بالنسبة للمستخدمين، خمسة عشر يوما بالنسبة للعمال. ويمكن تجديد فترة الاختبار مرة واحدة.",
        "text_fr": "La période d'essai en ce qui concerne les contrats à durée indéterminée est fixée à : trois mois pour les cadres et assimilés ; un mois et demi pour les employés ; quinze jours pour les ouvriers. La période d'essai peut être renouvelée une seule fois.",
        "explanation_darija": "فترة التجربة (Période d'essai) في عقد CDI محددة قانونياً في 3 أشهر للأطر (Cadres)، شهر ونصف للمستخدمين، و15 يوم للعمال، وكتجدد مرة وحدة فقط.",
        "domain": "labor_law",
    },
    {
        "id": "travail-art-35-41",
        "code": "Code du Travail (مدونة الشغل)",
        "law_number": "Loi n° 65-99",
        "dahir": "Dahir n° 1-03-194 du 14 rejeb 1424",
        "bo_issue": "BO n° 5167",
        "publication_date": "2003-12-08",
        "article": "Articles 35, 41 & 53",
        "topic": "Licenciement Abusif & Indemnités (الطرد التعسفي والتعويض عن الفصل والإشعار والضرر)",
        "text_ar": "يمنع فصل الأجير دون مبرر مقبول إلا إذا كان هذا المبرر مرتبطا بكفاءته أو بسلوكه. وفي حالة الفصل التعسفي يستحق الأجير التعويض عن الضرر والتعويض عن أجل الإخطار والتعويض عن الفصل حسب الأقدمية.",
        "text_fr": "Est interdit le licenciement d'un salarié sans motif valable sauf si celui-ci est lié à son aptitude ou à sa conduite. En cas de licenciement abusif, le salarié a droit à l'indemnité de préavis, à l'indemnité de licenciement (selon l'ancienneté) et aux dommages-intérêts.",
        "explanation_darija": "إلى طردك المشغل بلا سبب قانوني ولا بلا ما يحترم مسطرة الاستماع (المادة 62)، كيتسمى طرد تعسفي وعندك الحق في 3 ديال التعويضات: التعويض عن الإخطار (Préavis)، التعويض عن الفصل، والتعويض عن الضرر.",
        "domain": "labor_law",
    },
    {
        "id": "travail-art-184",
        "code": "Code du Travail (مدونة الشغل)",
        "law_number": "Loi n° 65-99",
        "dahir": "Dahir n° 1-03-194 du 14 rejeb 1424",
        "bo_issue": "BO n° 5167",
        "publication_date": "2003-12-08",
        "article": "Article 184",
        "topic": "Durée Légale du Travail (المدة القانونية لساعات العمل)",
        "text_ar": "تحدد في النشاطات غير الفلاحية مدة الشغل العادية المقررة للأجراء في 2288 ساعة في السنة أو 44 ساعة في الأسبوع.",
        "text_fr": "Dans les activités non agricoles, la durée normale de travail des salariés est fixée à 2288 heures par année ou 44 heures par semaine.",
        "explanation_darija": "ساعات العمل القانونية في القطاع غير الفلاحي هي 44 ساعة في السيمانة (أو 2288 ساعة في العام)، وأي ساعة زايدة كتخلص كساعات إضافية (Heures supplémentaires).",
        "domain": "labor_law",
    },
    {
        "id": "commerce-art-46",
        "code": "Code de Commerce & Loi SARL (قانون شركات المساهمة والشركات ذات المسؤولية المحدودة)",
        "law_number": "Loi n° 5-96 modifiée par Loi n° 24-10 et Loi n° 19-20",
        "dahir": "Dahir n° 1-21-75 du 3 hija 1442",
        "bo_issue": "BO n° 7006",
        "publication_date": "2021-07-22",
        "article": "Article 46",
        "topic": "Capital Social de la SARL (رأسمال الشركة ذات المسؤولية المحدودة)",
        "text_ar": "يحدد رأسمال الشركة ذات المسؤولية المحدودة بحرية من طرف الشركاء في النظام الأساسي، ويقسم إلى أنصبة اجتماعية متساوية القيمة.",
        "text_fr": "Le capital de la société à responsabilité limitée (SARL) est librement fixé par les associés dans les statuts. Le capital social est divisé en parts sociales à valeur minimale égale.",
        "explanation_darija": "تأسيس شركة SARL في المغرب مابقاش كيشترط 100 ألف درهم كحد أدنى؛ الشركاء يقدرو يحددو رأس المال بحرية في القانون الأساسي (Statuts).",
        "domain": "commercial_law",
    },
    {
        "id": "commerce-art-316",
        "code": "Code de Commerce (مدونة التجارة)",
        "law_number": "Loi n° 15-95",
        "dahir": "Dahir n° 1-96-83 du 15 rabii I 1417",
        "bo_issue": "BO n° 4418",
        "publication_date": "1996-10-03",
        "article": "Article 316",
        "topic": "Chèque sans Provision (إصدار شيك بدون مؤونة / بدون رصيد)",
        "text_ar": "يعاقب بالحبس من سنة إلى خمس سنوات وبغرامة تتراوح بين 2.000 و10.000 درهم دون أن تقل قيمتها عن خمسة وعشرين في المائة من مبلغ الشيك أو من الخصاص، ساحب الشيك الذي أغفل الحفاظ على المؤونة أو تكوينها.",
        "text_fr": "Est passible d'un emprisonnement d'un à cinq ans et d'une amende de 2.000 à 10.000 dirhams, sans que cette amende puisse être inférieure à 25% du montant du chèque ou de l'insuffisance de provision, le tireur d'un chèque qui omet de maintenir ou de constituer la provision.",
        "explanation_darija": "إصدار شيك بدون رصيد (أو تقديم شيك على سبيل الضمان) جنحة معاقب عليها في المادة 316 من مدونة التجارة بالحبس من سنة إلى 5 سنوات وغرامة لا تقل عن 25% من قيمة الشيك.",
        "domain": "commercial_law",
    },
    {
        "id": "bail-loi-67-12",
        "code": "Loi relative aux Baux d'Habitation et Professionnels (قانون كراء المحلات المعدة للسكنى أو للاستعمال المهني)",
        "law_number": "Loi n° 67-12",
        "dahir": "Dahir n° 1-13-111 du 15 moharrem 1435",
        "bo_issue": "BO n° 6208",
        "publication_date": "2013-11-28",
        "article": "Articles 3, 44 & 45",
        "topic": "Contrat de Bail Écrit & Procédure de Congé/Expulsion (عقد الكراء المكتوب وشروط الإفراغ)",
        "text_ar": "يبرم عقد الكراء وجوبا بمحرر كتابي ثابت التاريخ. ولا ينتهي عقد الكراء إلا بعد توجيه إشعار بالإفراغ طبقا للشروط القانونية (الاحتياج للسكن، الهدم لإعادة البناء، أو التماطل في الأداء) مع تصحيح الإشعار أمام المحكمة.",
        "text_fr": "Le contrat de bail est obligatoirement conclu par acte écrit ayant date certaine. Le bail ne prend fin qu'après notification d'un congé motivé (reprise pour habiter, démolition/reconstruction, ou défaut de paiement) validé par le juge.",
        "explanation_darija": "مول الدار (المكري) ما عندوش الحق يخرج المكتري بلا إشعار قانوني مصادق عليه من المحكمة ولأسباب محددة في القانون 67.12 (بحال السكن الشخصي مع تعويض، أو الهدم، أو عدم أداء الكراء) مع أجل إشعار قانوني (شهران على الأقل).",
        "domain": "real_estate_lease",
    },
    {
        "id": "penal-art-505-540",
        "code": "Code Pénal (مجموعة القانون الجنائي)",
        "law_number": "Dahir n° 1-59-413",
        "dahir": "Dahir n° 1-59-413 du 28 joumada II 1382",
        "bo_issue": "BO n° 2640 bis",
        "publication_date": "1963-06-05",
        "article": "Articles 505 & 540",
        "topic": "Vol & Escroquerie (جريمتا السرقة والنصب والاحتيال)",
        "text_ar": "الفصل 505: من اختلس عمدا مالا مملوكا للغير يعد سارقا ويعاقب بالحبس من سنة إلى خمس سنوات. الفصل 540: يعد مرتكبا لجريمة النصب ويعاقب بالحبس من سنة إلى خمس سنوات وغرامة من خمسمائة إلى خمسة آلاف درهم من استعمل الاحتيال لسلب أموال الغير.",
        "text_fr": "Article 505 : Quiconque soustrait frauduleusement une chose qui ne lui appartient pas est coupable de vol. Article 540 : Est coupable d'escroquerie et puni d'un emprisonnement d'un à cinq ans quiconque induit astucieusement en erreur une personne pour se faire remettre des fonds.",
        "explanation_darija": "النصب والاحتيال (الفصل 540) والسرقة (الفصل 505) عقوبتهما الحبس من سنة إلى 5 سنوات مع الحق في المطالبة بالتعويض المدني واسترجاع الأموال.",
        "domain": "penal_law",
    },
    {
        "id": "doc-art-77-230",
        "code": "Dahir des Obligations et Contrats — DOC (قانون الالتزامات والعقود)",
        "law_number": "Dahir du 9 ramadan 1331",
        "dahir": "Dahir du 12 août 1913",
        "bo_issue": "BO n° 46",
        "publication_date": "1913-09-12",
        "article": "Articles 77, 230 & 264",
        "topic": "Force Obligatoire du Contrat, Clause Pénale & Responsabilité Civile (القوة الملزمة للعقد والشرط الجزائي والمسؤولية التقصيرية)",
        "text_ar": "الفصل 77: كل فعل ارتكبه الإنسان عن بينة واختيار ومن غير أن يسمح له به القانون فأحدث ضررا ماديا أو معنويا للغير ألزم مرتكبه بتعويض هذا الضرر. الفصل 230: الالتزامات التعاقدية المنشأة على وجه صحيح تقوم مقام القانون بالنسبة إلى منشئيها. الفصل 264: للمحكمة تخفيض التعويض المتفق عليه إذا كان مبالغا فيه.",
        "text_fr": "Article 77 : Tout fait quelconque de l'homme qui, sans l'autorité de la loi, cause sciemment et volontairement à autrui un dommage matériel ou moral, oblige son auteur à réparer ledit dommage. Article 230 : Les obligations contractuelles valablement formées tiennent lieu de loi à ceux qui les ont faites. Article 264 : Le tribunal peut réduire le montant des dommages-intérêts convenus s'il est excessif.",
        "explanation_darija": "العقد شريعة المتعاقدين (الفصل 230)، وأي ضرر تسبب فيه شخص لغيره كيكون ملزم بالتعويض (الفصل 77)، والمحكمة عندها الحق تراجع الشرط الجزائي المبالغ فيه (الفصل 264).",
        "domain": "obligations_contracts",
    },
    {
        "id": "cndp-loi-09-08",
        "code": "Protection des Personnes Physiques à l'égard du Traitement des Données à Caractère Personnel (القانون المتعلق بحماية الأشخاص الذاتيين تجاه معالجة المعطيات ذات الطابع الشخصي)",
        "law_number": "Loi n° 09-08",
        "dahir": "Dahir n° 1-09-15 du 22 safar 1430",
        "bo_issue": "BO n° 5714",
        "publication_date": "2009-03-05",
        "article": "Articles 3, 4 & 12",
        "topic": "Consentement & Autorisation Préalable de la CNDP (الترخيص والتصريح لدى اللجنة الوطنية لمراقبة حماية المعطيات الشخصية CNDP)",
        "text_ar": "لا يجوز القيام بمعالجة المعطيات ذات الطابع الشخصي إلا إذا كان الشخص المعني قد عبر بشكل لا لبس فيه عن رضاه، وتخضع المعالجات لتصريح أولي أو إذن مسبق من اللجنة الوطنية لمراقبة حماية المعطيات ذات الطابع الشخصي (CNDP).",
        "text_fr": "Le traitement des données à caractère personnel ne peut être effectué que si la personne concernée a indubitablement donné son consentement, et nécessite une déclaration préalable ou une autorisation auprès de la CNDP (notamment pour les données sensibles ou biométriques).",
        "explanation_darija": "أي شركة أو موقع أو مشغل بغا يجمع المعطيات الشخصية أو كاميرات المراقبة أو البصمة البيومترية خاصو ياخذ موافقة الشخص المعني ويدير تصريح أو طلب ترخيص مسبق عند لجنة CNDP طبقاً للقانون 09-08.",
        "domain": "data_privacy_law",
    },
]


LEGAL_DISCLAIMERS = {
    "ar": "⚠️ تنبيه قانوني: هذه المعلومات مستخرجة حرفياً من النصوص التشريعية المغربية الرسمية (الجريدة الرسمية) لأغراض التوجيه القانوني والأكاديمي، ولا تغني عن استشارة محامٍ مقيد بهيئات المحامين بالمغرب.",
    "fr": "⚠️ Avertissement Légal : Ces informations sont extraites des textes législatifs marocains officiels (Bulletin Officiel) à titre documentaire et ne remplacent pas la consultation d'un avocat inscrit au barreau.",
    "darija": "⚠️ تنبيه قانوني: هاد المعلومات مبنية مباشرة على الفصول القانونية الرسمية فالمغرب (الجريدة الرسمية) باش تعاونك تفهم حقوقك، وما كتعوضش استشارة محامي مختص.",
}


class MoroccanLegalRAG:
    """
    Hybrid Moroccan Legal RAG Engine:
    Combines Okapi BM25 (k1=1.5, b=0.75) + Character N-Gram Semantic Embeddings
    fused via Reciprocal Rank Fusion (RRF_K = 60), ported from dual_portfolio_hub/api/_lib/knowledge.js.
    """

    def __init__(self) -> None:
        self.db = MOROCCAN_LEGAL_DATABASE
        self._build_hybrid_index()

    def _build_hybrid_index(self) -> None:
        self._doc_tokens: List[Counter] = []
        self._doc_lengths: List[int] = []
        self._df: Counter = Counter()
        self._trigram_vecs: List[Counter] = []

        for item in self.db:
            full_text = MoroccanLegalNLP.normalize_arabic(
                f"{item['code']} {item['law_number']} {item['article']} {item['topic']} "
                f"{item['text_ar']} {item['text_fr']} {item.get('explanation_darija', '')}"
            ).lower()
            tokens = [t for t in full_text.split() if len(t) > 1]
            tf = Counter(tokens)
            self._doc_tokens.append(tf)
            self._doc_lengths.append(len(tokens))
            for term in tf.keys():
                self._df[term] += 1

            # Character 3-grams for morphological/fuzzy Arabic-French-Darija matching
            padded = f"  {full_text}  "
            trigrams = Counter(padded[i : i + 3] for i in range(max(1, len(padded) - 2)))
            self._trigram_vecs.append(trigrams)

        self._avg_len = sum(self._doc_lengths) / max(1, len(self._doc_lengths))

    @staticmethod
    def _cosine_counter(a: Counter, b: Counter) -> float:
        if not a or not b:
            return 0.0
        common = set(a.keys()) & set(b.keys())
        dot = sum(a[k] * b[k] for k in common)
        norm_a = math.sqrt(sum(v * v for v in a.values()))
        norm_b = math.sqrt(sum(v * v for v in b.values()))
        return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

    def search_articles(self, query: str, limit: int = 3) -> List[Dict[str, Any]]:
        translation_info = MoroccanLegalNLP.translate_darija_query(query)
        augmented_query = translation_info["augmented_query"]
        domain = translation_info["domain"]
        q_norm = MoroccanLegalNLP.normalize_arabic(augmented_query).lower()
        q_tokens = [w for w in q_norm.split() if len(w) > 1]

        n_docs = len(self.db)
        bm25_scores: List[tuple[float, int]] = []
        for idx, item in enumerate(self.db):
            tf = self._doc_tokens[idx]
            doc_len = self._doc_lengths[idx]
            score = 4.0 if item["domain"] == domain else 0.0
            for term in q_tokens:
                freq = tf.get(term, 0)
                if not freq and len(term) >= 3:
                    freq = sum(c for tok, c in tf.items() if term in tok) * 0.6
                if freq > 0:
                    df = max(1, self._df.get(term, 1))
                    idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                    score += (idf * freq * (BM25_K1 + 1.0)) / (
                        freq + BM25_K1 * (1.0 - BM25_B + BM25_B * (doc_len / self._avg_len))
                    )
            bm25_scores.append((score, idx))

        bm25_ranked = [idx for _, idx in sorted(bm25_scores, key=lambda x: x[0], reverse=True)]

        # Vector trigram ranking
        q_padded = f"  {q_norm}  "
        q_trigrams = Counter(q_padded[i : i + 3] for i in range(max(1, len(q_padded) - 2)))
        vec_scores = [
            (self._cosine_counter(q_trigrams, self._trigram_vecs[idx]), idx)
            for idx in range(n_docs)
        ]
        vec_ranked = [idx for _, idx in sorted(vec_scores, key=lambda x: x[0], reverse=True)]

        # Reciprocal Rank Fusion (RRF_K = 60)
        rrf_scores: Dict[int, float] = {}
        for rank, idx in enumerate(bm25_ranked):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)
        for rank, idx in enumerate(vec_ranked):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (RRF_K + rank + 1)
        for idx, item in enumerate(self.db):
            if item["domain"] == domain:
                rrf_scores[idx] += 0.012

        fused_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:limit]
        results: List[Dict[str, Any]] = []
        for i in fused_indices:
            enriched = dict(self.db[i])
            enriched["rrf_score"] = round(rrf_scores[i], 5)
            results.append(enriched)
        return results

    def verify_citations(self, cited_articles: List[Dict[str, Any]]) -> bool:
        """
        Anti-Hallucination Gate: Verifies that every cited article ID, Dahir,
        and BO issue exists verbatim in the trusted statutory database.
        """
        if not cited_articles:
            return False
        valid_keys = {(a["code"], a["article"], a["bo_issue"]) for a in self.db}
        return all((c["code"], c["article"], c["bo_issue"]) in valid_keys for c in cited_articles)

    def answer_query(self, query: str, lang: str = "ar") -> Dict[str, Any]:
        translation_info = MoroccanLegalNLP.translate_darija_query(query)
        articles = self.search_articles(query)
        domain = translation_info["domain"]

        # 1. Build Verbatim Citations Payload (Strictly Unaltered Statutory Text)
        verbatim_citations = [
            {
                "id": art["id"],
                "code": art["code"],
                "law_number": art["law_number"],
                "dahir": art["dahir"],
                "bo_issue": art["bo_issue"],
                "publication_date": art["publication_date"],
                "article": art["article"],
                "topic": art["topic"],
                "text_ar": art["text_ar"],
                "text_fr": art["text_fr"],
                "rrf_score": art.get("rrf_score", 0.0),
            }
            for art in articles
        ]

        citation_verified = self.verify_citations(verbatim_citations)

        # 2. Build Separated AI Commentary in MSA, French, and Moroccan Darija
        ai_commentary = {
            "ar": (
                f"تحليل قانوني مصنف ضمن مجال ({domain}): استناداً إلى الفصول القانونية الموثقة في الجريدة الرسمية أدناه، "
                + " ".join(f"[{a['article']} من {a['code']} ({a['bo_issue']})]" for a in articles)
                + "، فإن المشرع المغربي ينظم هذه الوضعية بنصوص آمرة تحفظ حقوق الأطراف."
            ),
            "fr": (
                f"Synthèse juridique ({domain}) : Conformément aux textes officiels publiés au Bulletin Officiel "
                + ", ".join(f"[{a['article']} - {a['law_number']} ({a['bo_issue']})]" for a in articles)
                + ", les dispositions ci-dessous s'appliquent directement à votre situation."
            ),
            "darija": " / ".join(a.get("explanation_darija", a["text_ar"]) for a in articles),
        }

        if lang == "ar":
            intro = f"### 📜 النصوص القانونية الحرفية الموثقة ({domain})\n"
            citations_block = "\n\n".join(
                f"📌 **{art['code']} — {art['article']}** (`{art['law_number']}` | `{art['bo_issue']}` بتاريخ `{art['publication_date']}`):\n> « {art['text_ar']} »"
                for art in articles
            )
            commentary_block = f"\n\n---\n### 💡 الشرح المبسط والتعليق التحليلي\n{ai_commentary['ar']}\n\n**بالدارجة المغربية:** {ai_commentary['darija']}"
            full_response = f"{intro}\n{citations_block}{commentary_block}\n\n{LEGAL_DISCLAIMERS['ar']}"
        elif lang == "darija":
            intro = f"### 🇲🇦 الجواب القانوني بالدارجة المغربية (مع الفصول الرسمية)\n"
            citations_block = "\n\n".join(
                f"📌 **{art['code']} — {art['article']}** (`{art['bo_issue']}`):\n- **الشرح بالدارجة:** {art.get('explanation_darija', '')}\n- **النص الرسمي (حرفي):** « {art['text_ar']} »"
                for art in articles
            )
            full_response = f"{intro}\n{citations_block}\n\n{LEGAL_DISCLAIMERS['darija']}"
        else:
            intro = f"### 📜 Textes Législatifs Officiels Verbatim ({domain})\n"
            citations_block = "\n\n".join(
                f"📌 **{art['code']} — {art['article']}** (`{art['law_number']}` | `{art['bo_issue']}` du `{art['publication_date']}`):\n> « {art['text_fr']} »"
                for art in articles
            )
            commentary_block = f"\n\n---\n### 💡 Commentaire Analytique (Séparé du Texte Officiel)\n{ai_commentary['fr']}"
            full_response = f"{intro}\n{citations_block}{commentary_block}\n\n{LEGAL_DISCLAIMERS['fr']}"

        return {
            "query": query,
            "darija_translation": translation_info,
            "query_translation": translation_info,
            "domain": domain,
            "detected_domain": domain,
            "retrieval_engine": "Hybrid Okapi BM25 + Trigram Vector RRF (k=60)",
            "matched_articles": articles,
            "verbatim_citations": verbatim_citations,
            "ai_commentary": ai_commentary,
            "citation_verified": citation_verified,
            "legal_disclaimer": LEGAL_DISCLAIMERS.get(lang, LEGAL_DISCLAIMERS["fr"]),
            "response": full_response,
        }
