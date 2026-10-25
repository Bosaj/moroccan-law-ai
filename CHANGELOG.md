# Changelog

All notable changes to **Mizan (moroccan-law-ai)** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/), and this project adheres to [Semantic Versioning](https://semver.org/).

---

## [1.2.0] - 2026-10-25
### Added
- **Moroccan Official Legal PDF Archive (`src/download_laws.py`):**
  - Automated downloader and synchronization engine pulling real, official *Bulletin Officiel* (الجريدة الرسمية) PDF editions directly from the Moroccan General Secretariat of the Government (`sgg.gov.ma`).
  - Bilingual coverage across all major statutory domains:
    1. **Code de la Famille / مدونة الأسرة (Loi 70-03):** Official Arabic BO 5184 + French BO 5184.
    2. **Code de la Route / مدونة السير (Loi 52-05):** Official Arabic BO 5878 + French BO 5888.
    3. **Réforme du Code de la Route (Loi 116-14):** Official Arabic BO 6496 + French BO 6496.
    4. **Code du Travail / مدونة الشغل (Loi 65-99):** Official Arabic BO 5167 + French BO 5210.
    5. **Code de Commerce (Loi 15-95):** Official Arabic BO 4418 + French BO 4482.
    6. **Sociétés Anonymes & SARL (Loi 17-95 & 5-96):** Official Arabic BO 4422 + French BO 4418.
    7. **Protection des Données Personnelles CNDP (Loi 09-08):** Official Arabic BO 5711 + French BO 5744.
    8. **Baux d'Habitation et Professionnels (Loi 67-12):** Official Arabic BO 6208 + French BO 6240.
    9. **Code des Droits Réels (Loi 39-08):** Official Arabic BO 5998 + French BO 6022.
    10. **Protection du Consommateur (Loi 31-08):** Official Arabic BO 5932 + French BO 5932.
    11. **Violences Faites aux Femmes / Code Pénal (Loi 103-13):** Official Arabic BO 6655 + French BO 6706.
    12. **Modernisation des Sociétés Commerciales & SAS (Loi 19-20 / 20-19):** Official Arabic BO 6975 + French BO 7010.
  - Manifest catalog (`data/laws_pdf/manifest.json`) indexing all downloaded files, sizes, publication dates, and original SGG download URLs.
  - REST endpoint `/api/laws-pdf` in `server.py` to inspect and download stored statutory PDFs.
- **Graceful Shutdown Handling:**
  - Added clean `KeyboardInterrupt` trap in `server.py` to prevent stack traces on user termination (`Ctrl+C`).
- **Comprehensive Project Wiki:**
  - Rebuilt `wiki/` documentation covering system architecture, RAG retrieval mathematical formulation, Darija NLP dictionary, redline engine specifications, and deployment guides.

---

## [1.1.0] - 2026-10-25
### Added
- **Mizan (ميزان) Bespoke React 19 Frontend:**
  - Production-grade Single-Page Application (`web/`) built with React 19, TypeScript, Vite, and Tailwind CSS v4, completely superseding the legacy Streamlit interface.
  - Authentic Moroccan sovereign legal broadsheet design:
    - Maghribi calligraphy (`BouazziMaghribi.woff2`) for royal Dahir seals and headers.
    - IBM Plex Sans Arabic for crisp legal typography.
    - Warm charcoal & brass chamber palette with octagonal zellige Mizan scale icon.
  - True Bi-Directional RTL Mirroring: switching to Arabic dynamically sets `dir="rtl"` and `lang="ar"`, with complete layout and navigation mirroring.
  - Four interactive legal tech views:
    1. *Consultation Juridique:* Darija translation badge, verbatim statutory citations, and plain-language commentary.
    2. *Veille Bulletin Officiel:* Searchable catalogue of 18 Official Gazette issues with audience filtering.
    3. *Comparateur de Réformes:* Side-by-side legal text comparator with word-level redline diffs and token-level change metrics.
    4. *Audit de Contrats:* Contract screener with animated SVG `RiskDial` gauge, statutory nullity alerts, and bilingual remediation advice.
- **Frontend Test Suite:**
  - 7 Vitest integration and unit tests covering navigation, i18n switching, redline diff rendering, and risk gauges (`web/src/App.test.tsx`).
- **Unified Full-Stack Server Integration:**
  - `server.py` natively serves both the JSON REST API (`/api/*`) and the compiled production bundle (`web/dist/`) on port 8090 with strict CSP headers and directory traversal protection.

---

## [1.0.0] - 2026-10-24
### Added
- **Grounded Moroccan Statutory RAG (`src/legal_rag.py`):**
  - Hybrid Okapi BM25 (`k1=1.5`, `b=0.75`) + Character Trigram Vector Cosine Reciprocal Rank Fusion (`RRF_K=60`).
  - Strict separation of verbatim statutory citations vs. AI analytical commentary.
  - Anti-hallucination verification gate rejecting any unverified article citation.
  - 7 Moroccan legal domains covered (Family Law, Labor Law, Commercial Code, Leases, Criminal Law, Obligations & Contracts, CNDP Privacy).
- **Moroccan Darija NLP Bridge (`src/arabic_nlp.py`):**
  - Translates everyday Moroccan Darija queries (both Arabic script and Arabizi) into formal statutory search terms.
- **Official Gazette Redline Diff Engine (`src/bo_diff_engine.py`):**
  - Computes word-level `<del>` / `<ins>` redline diffs between prior law and new *Bulletin Officiel* reforms.
  - Scores compliance severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and generates trilingual executive summaries.
- **Moroccan Contract Compliance Auditor (`src/contract_auditor.py`):**
  - Scans Moroccan employment contracts (*CDI/CDD*) and residential leases for statutory nullities.
- **REST API Server & SQLite Audit Store (`server.py`):**
  - Threading HTTP server with persistent SQLite audit logging.
- **Test Suite:**
  - Automated tests covering NLP, Legal RAG, and BO diffing with 100% pass rate.

---

## [0.1.0] - 2026-10-18
### Added
- Initial repository scaffold and data structure outlines.
