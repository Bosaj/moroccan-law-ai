# 5. REST API Reference

The sovereign server (`server.py`) exposes a RESTful JSON API on port 8090 (or environment variable `$PORT`).

---

### `GET /api/health`
Returns system status, active database counts, and search engine parameters.
```json
{
  "status": "ok",
  "app": "moroccan-law-ai",
  "retrieval_engine": "Hybrid Okapi BM25 + Trigram Vector RRF (k=60)",
  "corpus_articles_count": 50,
  "bo_issues_count": 18,
  "consultations_logged": 12,
  "audits_logged": 4
}
```

---

### `POST /api/query`
Executes a grounded statutory search across Moroccan codes with Darija translation and anti-hallucination verification.
* **Request Body:**
  ```json
  {
    "query": "ما هو أجل الإخطار قبل إنهاء عقد الشغل؟",
    "lang": "ar"
  }
  ```
* **Response:**
  ```json
  {
    "query": "...",
    "domain": "labor_law",
    "citation_verified": true,
    "matched_articles": [ ... ],
    "verbatim_citations": [
      {
        "id": "travail-art-43",
        "code": "Code du Travail (مدونة الشغل)",
        "law_number": "Loi n° 65-99",
        "bo_issue": "BO n° 5167",
        "article": "Article 43",
        "text_ar": "يبدأ أجل الإخطار...",
        "text_fr": "Le délai de préavis court..."
      }
    ],
    "simplified_explanation": {
      "ar": "...",
      "fr": "...",
      "darija": "..."
    },
    "legal_disclaimer": "..."
  }
  ```

---

### `GET /api/bo-issues[?audience={audience}]`
Lists indexed Moroccan Official Gazette issues.
* **Query Parameters:** `audience` (optional: `citizens`, `smes`, `hr`, `lawyers`, `accountants`, `startups`).
* **Response:**
  ```json
  {
    "count": 18,
    "issues": [ ... ]
  }
  ```

---

### `POST /api/bo-diff`
Computes a word-level redline diff between two legal texts.
* **Request Body:**
  ```json
  {
    "old_text": "Texte ancien de l'article",
    "new_text": "Texte nouveau modifié par la réforme",
    "article_ref": "Article 14",
    "bo_issue": "BO n° 7398"
  }
  ```
* **Response:**
  ```json
  {
    "article_ref": "Article 14",
    "added_tokens": [ "modifié", "par", "la", "réforme" ],
    "removed_tokens": [ "ancien" ],
    "change_ratio": 0.35,
    "similarity_ratio": 0.65,
    "compliance_severity": "MEDIUM",
    "redline_html": "Texte <del>ancien</del> <ins>nouveau modifié par la réforme</ins>",
    "redline_markdown": "Texte [-ancien-] {+nouveau modifié par la réforme+}"
  }
  ```

---

### `POST /api/audit-contract`
Scans contractual clauses for statutory nullities under Moroccan law.
* **Request Body:**
  ```json
  {
    "contract_text": "La durée de travail hebdomadaire est fixée à 55 heures sans majoration.",
    "lang": "fr"
  }
  ```
* **Response:**
  ```json
  {
    "status": "NON_COMPLIANT_HIGH_RISK",
    "risk_score": 85,
    "violations_count": 1,
    "violations": [
      {
        "id": "statutory_working_hours",
        "category": "Durée légale de travail",
        "severity": "HIGH",
        "explanation": "Durée supérieure aux 44 heures légales par semaine.",
        "statutory_basis": "Article 184 du Code du Travail (BO n° 5167)",
        "remediation_fr": "Ajuster à 44 heures par semaine maximum.",
        "remediation_ar": "تعديل ساعات العمل إلى 44 ساعة أسبوعياً كحد أقصى."
      }
    ],
    "disclaimer": "..."
  }
  ```

---

### `GET /api/laws-pdf`
Returns the manifest of all 24 downloaded Moroccan official law PDFs.
* **Response:**
  ```json
  {
    "institution": "Secrétariat Général du Gouvernement (sgg.gov.ma)",
    "total_files_downloaded": 24,
    "total_archive_size_mb": 83.53,
    "laws": [ ... ]
  }
  ```
