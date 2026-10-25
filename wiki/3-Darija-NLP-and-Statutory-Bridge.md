# 3. Moroccan Darija NLP & Statutory Translation Bridge

## 3.1 The Linguistic Challenge

Moroccan citizens and workers overwhelmingly express legal dilemmas in **Moroccan Darija** (الدارجة المغربية) or **Arabizi** (Latin numbers & letters, e.g., `3` for ع, `7` for ح, `9` for ق). However, Moroccan legislation is codified exclusively in **Modern Standard Arabic (MSA)** and official **French**.

A search query like `"جراو عليا من الخدمة بلا سابق إنذار"` or `"moul dar bgha ykhrjni bla ma y3lemni"` yields **zero results** in standard lexical search systems.

## 3.2 Linguistic Normalization & Domain Detection (`src/arabic_nlp.py`)

The `MoroccanLegalNLP` module executes a multi-stage pipeline:

1. **Script Detection & Orthographic Normalization:**
   - Detects whether the query is Arabic script, Arabizi (Latin script with digit phonemes), or standard French.
   - Normalizes Arabic variants (unifying `أ`, `إ`, `آ` $\rightarrow$ `ا`, `ة` $\rightarrow$ `ه`, `ى` $\rightarrow$ `ي`, stripping Tatweel `ـ`, and removing Tashkeel / diacritics).

2. **Domain Classification:**
   - Analyzes lexical triggers to classify the legal domain into:
     - `labor_law` (مدونة الشغل — Loi 65-99)
     - `family_law` (مدونة الأسرة — Loi 70-03)
     - `real_estate_lease` (الكراء السكني والمهني — Loi 67-12)
     - `commercial_law` (مدونة التجارة وقانون الشركات — Loi 15-95 / 5-96)
     - `criminal_law` (مجموعة القانون الجنائي)
     - `civil_law` (قانون الالتزامات والعقود — DOC)
     - `data_protection` (حماية المعطيات الشخصية — Loi 09-08)

3. **Query Expansion & Statutory Translation:**
   Expands vernacular expressions into formal legislative keywords:
   - `"جراو عليا"` / `"tarad"` $\rightarrow$ `فصل تعسفي`, `طرد تعسفي`, `licenciement abusif`, `تعويض عن الفصل`
   - `"سابق إنذار"` / `"bla preavis"` $\rightarrow$ `أجل الإخطار`, `délai de préavis`, `المادة 43`
   - `"فترة تجربة"` $\rightarrow$ `فترة الاختبار`, `période d'essai`, `المادة 14`
   - `"موال الدار"` / `"moul lkhedma"` $\rightarrow$ `المكري`, `المشغل`, `bailleur`, `employeur`
   - `"النفقة"` / `"tlak"` $\rightarrow$ `الطلاق`, `التطليق للشقاق`, `مستحقات الزوجة والأبناء`, `المادة 84`

4. **Augmented Query Construction:**
   Constructs a composite query that feeds the Okapi BM25 and Trigram Vector rankers with both original tokens and authoritative statutory legal terms.
