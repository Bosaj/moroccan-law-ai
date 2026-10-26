import unittest
from src.arabic_nlp import MoroccanLegalNLP


class TestMoroccanLegalNLPDeep(unittest.TestCase):
    def test_normalize_empty_and_none(self):
        self.assertEqual(MoroccanLegalNLP.normalize_arabic(""), "")
        self.assertEqual(MoroccanLegalNLP.normalize_arabic(None), "")

    def test_normalize_diacritics_and_tatweel(self):
        # Tashkeel / diacritics
        text_with_harakat = "مُدَوَّنَةُ الأُسْرَةِ وَقَانُونُ الشُّغْلِ"
        normalized = MoroccanLegalNLP.normalize_arabic(text_with_harakat)
        self.assertNotIn("ُ", normalized)
        self.assertNotIn("َ", normalized)
        self.assertNotIn("ّ", normalized)
        self.assertNotIn("ِ", normalized)

        # Tatweel / Kashida
        text_with_tatweel = "مــــحــــكــــمــــة"
        self.assertEqual(MoroccanLegalNLP.normalize_arabic(text_with_tatweel), "محكمه")

    def test_normalize_alif_variants(self):
        # إ, أ, آ should all normalize to ا
        samples = ["إشعار", "أجير", "آجال", "اقتطاع"]
        for s in samples:
            norm = MoroccanLegalNLP.normalize_arabic(s)
            self.assertTrue(norm.startswith("ا"), f"Failed for {s} -> {norm}")

    def test_normalize_taa_marbuta_and_alif_maqsura(self):
        # ة -> ه
        self.assertEqual(MoroccanLegalNLP.normalize_arabic("مدونة"), "مدونه")
        self.assertEqual(MoroccanLegalNLP.normalize_arabic("محكمة"), "محكمه")

        # ى -> ي
        self.assertEqual(MoroccanLegalNLP.normalize_arabic("دعوى"), "دعوي")
        self.assertEqual(MoroccanLegalNLP.normalize_arabic("فتوى"), "فتوي")

    def test_darija_labor_law_expressions(self):
        queries = [
            "جراو عليا من الخدمة شنو المعمول؟",
            "طردوني بلا سابق إنذار وبغيت تعويض",
            "خرجوني من الخدمة بعد 5 سنين",
            "jraw 3liya lbarh mn lkhdma",
            "patron tardouni bla sbab",
        ]
        for q in queries:
            res = MoroccanLegalNLP.translate_darija_query(q)
            self.assertTrue(res["detected_darija"], f"Expected Darija detected for: {q}")
            self.assertEqual(res["domain"], "labor_law", f"Expected labor_law for: {q}")
            self.assertGreater(len(res["expanded_terms"]), 0)

    def test_darija_real_estate_lease_expressions(self):
        queries = [
            "مول الدار باغي يخرجني وخا مخلص الكرا",
            "moul dar bgha ykhrjni bla ma y3lemni",
            "3andi mochkil f lkra dyal dar",
        ]
        for q in queries:
            res = MoroccanLegalNLP.translate_darija_query(q)
            self.assertTrue(res["detected_darija"], f"Expected Darija detected for: {q}")
            self.assertEqual(res["domain"], "real_estate_lease", f"Expected real_estate_lease for: {q}")
            self.assertIn("Loi 67-12", " ".join(res["expanded_terms"]))

    def test_darija_commercial_law_expressions(self):
        queries = [
            "عطاوه شيك بدون رصيد شنو يدير؟",
            "3tani cheque khawi f lbi3",
            "cheque bla rssid chno l3o9oba dyalo",
        ]
        for q in queries:
            res = MoroccanLegalNLP.translate_darija_query(q)
            self.assertTrue(res["detected_darija"], f"Expected Darija detected for: {q}")
            self.assertEqual(res["domain"], "commercial_law", f"Expected commercial_law for: {q}")
            self.assertIn("316", " ".join(res["expanded_terms"]))

    def test_darija_family_law_expressions(self):
        queries = [
            "بغيت نطلب طلاق الشقاق والنفقة للدراري",
            "bghit nafa9a d drari mn b3d tla9",
            "hadana dyal lbnat mn b3d tlaq",
        ]
        for q in queries:
            res = MoroccanLegalNLP.translate_darija_query(q)
            self.assertTrue(res["detected_darija"], f"Expected Darija detected for: {q}")
            self.assertEqual(res["domain"], "family_law", f"Expected family_law for: {q}")

    def test_darija_penal_law_expressions(self):
        queries = [
            "نصبو عليا ف بيعة وشرية ف طوموبيل",
            "nsbou 3liya f floussi",
            "khdaw liya floussi b lhila",
        ]
        for q in queries:
            res = MoroccanLegalNLP.translate_darija_query(q)
            self.assertTrue(res["detected_darija"], f"Expected Darija detected for: {q}")
            self.assertEqual(res["domain"], "penal_law", f"Expected penal_law for: {q}")
            self.assertIn("540", " ".join(res["expanded_terms"]))

    def test_darija_conversational_particles(self):
        particles_samples = [
            ("شنو هو القانون فهاد الحالة؟", True),
            ("واش عندي الحق نطالب بالتعويض؟", True),
            ("كيفاش ندير شكاية؟", True),
            ("علاش نقصو ليا من الصالير؟", True),
            ("wach momkin ndir da3wa?", True),
        ]
        for query, expected_darija in particles_samples:
            res = MoroccanLegalNLP.translate_darija_query(query)
            self.assertEqual(res["detected_darija"], expected_darija, f"Failed for {query}")

    def test_classify_legal_domain_all_domains(self):
        domain_cases = [
            ("شروط عقد الزواج وحضانة الأطفال وإسقاط النفقة", "family_law"),
            ("طرد تعسفي وأجل الإخطار وساعات العمل الإضافية في مدونة الشغل", "labor_law"),
            ("جريمة السرقة الموصوفة والاحتيال والغرامة في القانون الجنائي", "penal_law"),
            ("تأسيس شركة ذات مسؤولية محدودة والكمبيالة والسجل التجاري", "commercial_law"),
            ("المسؤولية التقصيرية والتعويض عن الضرر وفسخ العقد في قانون الالتزامات والعقود", "obligations_contracts"),
            ("عقد كراء المحلات السكنية ودعوى الإفراغ والتحفيظ العقاري", "real_estate_lease"),
            ("حماية المعطيات ذات الطابع الشخصي وترخيص كاميرات المراقبة CNDP", "data_privacy_law"),
        ]
        for text, expected in domain_cases:
            detected = MoroccanLegalNLP.classify_legal_domain(text)
            self.assertEqual(detected, expected, f"Failed for text: {text}")

    def test_classify_unknown_fallback(self):
        # Query with no legal keywords should fall back to general_law
        fallback = MoroccanLegalNLP.classify_legal_domain("صباح الخير كيف حالك اليوم الطقس مشمس")
        self.assertEqual(fallback, "general_law")


if __name__ == "__main__":
    unittest.main()
