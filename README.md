# ⚖️ Mizan (ميزان) — Moroccan Law AI + Official Gazette (*Jarida Rasmiya*) Redline Engine

> **Unified Moroccan Legal Tech Platform (Master Dossier Ideas #07 + #17):** Grounded Moroccan Statutory Q&A in **Arabic (MSA)**, **Français**, and **Moroccan Darija** (Arabic & Arabizi scripts), paired with an **Official Gazette (*Bulletin Officiel* — الجريدة الرسمية `sgg.gov.ma`) Article-by-Article Redline Diff & Compliance Alert Engine**, a **Moroccan Contract Compliance Auditor**, and a **Complete Archive of Official Moroccan Law PDFs (Arabic & French)**. Powered by a bespoke, high-performance **React 19 + TypeScript + Vite + Tailwind CSS** frontend (*Mizan* · ميزان).

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v4-38bdf8.svg)](https://tailwindcss.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-20%2F20%20Passing-emerald.svg)](https://vitest.dev/)
[![Official Laws](https://img.shields.io/badge/Official%20PDFs-24%20Laws%20(83.5%20MB)-amber.svg)](data/laws_pdf/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Author:** Oussama Elhadji (`@Bosaj`) — `oussousselhadji@gmail.com`

---

## 🌟 Core Capabilities

### 1. Grounded Moroccan Legal RAG with Strict Citation Safety (`src/legal_rag.py`)
- **Strict Separation of Verbatim Law vs. AI Commentary:**
  - `verbatim_citations`: Immutable statutory blocks citing the exact **Dahir**, **Law Number**, **Bulletin Officiel Issue #**, **Publication Date**, and **Article Number** in both Arabic and French.
  - `ai_commentary`: Separate simplified explanation in **Moroccan Darija**, **Modern Standard Arabic (MSA)**, and **French**.
- **Anti-Hallucination Verification Gate (`verify_citations`):** Rejects any response whose cited article ID is not verified in the retrieved statutory corpus.
- **7 Moroccan Legal Domains Covered:**
  - **مدونة الأسرة** (*Moudawana* — Loi 70-03, BO n° 5184)
  - **مدونة الشغل** (*Code du Travail* — Loi 65-99, BO n° 5167)
  - **مدونة التجارة وقانون الشركات** (*Code de Commerce / SARL* — Loi 15-95 / Loi 5-96 / Loi 19-20)
  - **الكراء السكني والمهني** (*Baux d'habitation* — Loi 67-12, BO n° 6208)
  - **مجموعة القانون الجنائي** (*Code Pénal* — Loi 103-13 / Loi 03-23)
  - **قانون الالتزامات والعقود** (*DOC* — Dahir 1913)
  - **حماية المعطيات ذات الطابع الشخصي** (*CNDP* — Loi 09-08, BO n° 5711)

### 2. Moroccan Darija → Legal Query Bridge (`src/arabic_nlp.py`)
- Translates everyday Moroccan Darija questions (both Arabic script e.g. `"جراو عليا من الخدمة بلا سابق إنذار"` and Latin Arabizi e.g. `"moul dar bgha ykhrjni mn lkra bla ma y3lemni"`) into formal statutory search terms across Moroccan labor, family, lease, commercial, criminal, and data privacy codes.

### 3. Official Gazette (*Jarida Rasmiya* — الجريدة الرسمية) Redline Diff Engine (`src/bo_diff_engine.py`)
- Computes word-level `<del>` / `<ins>` redline diffs between prior statutory text and newly promulgated *Bulletin Officiel* reforms from `sgg.gov.ma`.
- Scores compliance severity (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and provides trilingual executive summaries (**Darija**, **Arabic MSA**, **French**) filterable by target audience (`SMEs`, `Accountants`, `HR`, `Corporate Lawyers`, `DPOs`, `Tech Startups`).

### 4. Moroccan Contract Compliance Auditor (`src/contract_auditor.py`)
- Scans Moroccan employment contracts (*CDI/CDD*), residential/commercial leases (*Baux*), and data privacy clauses for statutory nullities (e.g., excessive probation periods violating *Code du Travail Art. 14*, advance waiver of severance violating *Art. 41 & 51*, or undeclared biometric processing violating *Loi 09-08 CNDP*).

### 5. Moroccan Official Law PDF Archive (`src/download_laws.py`)
- **24 Real Official PDF Codes & Enactments (83.5 MB)** downloaded directly from the Moroccan General Secretariat of the Government (`sgg.gov.ma`):
  - Every law is provided in both **Arabic (Édition Générale)** and **French (Traduction Officielle)**:
    1. **Code de la Famille / مدونة الأسرة** (Loi 70-03) [AR & FR]
    2. **Code de la Route / مدونة السير** (Loi 52-05) [AR & FR]
    3. **Réforme du Code de la Route** (Loi 116-14) [AR & FR]
    4. **Code du Travail / مدونة الشغل** (Loi 65-99) [AR & FR]
    5. **Code de Commerce** (Loi 15-95) [AR & FR]
    6. **Sociétés Anonymes & SARL** (Loi 17-95 & 5-96) [AR & FR]
    7. **Protection des Données CNDP** (Loi 09-08) [AR & FR]
    8. **Baux d'Habitation et Professionnels** (Loi 67-12) [AR & FR]
    9. **Code des Droits Réels** (Loi 39-08) [AR & FR]
    10. **Protection du Consommateur** (Loi 31-08) [AR & FR]
    11. **Violences Faites aux Femmes / Code Pénal** (Loi 103-13) [AR & FR]
    12. **Modernisation des Sociétés Commerciales & SAS** (Loi 19-20) [AR & FR]
- Indexed with manifest (`data/laws_pdf/manifest.json`) and exposed via `/api/laws-pdf` and direct streaming `/data/laws_pdf/*`.

### 6. Production-Grade Trilingual React Frontend (*Mizan* · ميزان) (`web/`)
- Bespoke Moroccan sovereign legal design system:
  - Authentic Moroccan Maghribi calligraphy (`BouazziMaghribi.woff2`) for headers and royal Dahir seals.
  - IBM Plex Sans Arabic for crisp legal typography in Modern Standard Arabic with full bidirectional RTL mirroring (`dir="rtl"`).
  - Warm charcoal & brass chamber palette with double-bezel borders and gold accents (`#d97706`, `#b45309`).
  - Interactive tabs:
    1. **Consultation Juridique:** Real-time Moroccan legal Q&A with Darija translation badges, verbatim bilingual statutory citations, and plain-language commentary.
    2. **Veille Bulletin Officiel:** Searchable database of 18 BO issues with audience filtering and article amendment breakdowns.
    3. **Comparateur de Réformes:** Side-by-side legal text comparator with word-level redline diffs and token-level change metrics.
    4. **Audit de Contrats:** Paste any Moroccan contract for instant compliance scoring, RiskDial SVG gauge, flagged illegal clauses, and actionable remediation steps.

---

## 🚀 Quickstart

### 1. Download & Synchronize Official Moroccan Law PDFs (83.5 MB)
```bash
python src/download_laws.py
```

### 2. Run Automated Unit & API Tests (Python Backend)
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 3. Frontend Development & Build (`web/`)
```bash
cd web
npm install
npm test            # Run Vitest test suite (7 tests)
npm run typecheck   # Typecheck with TypeScript
npm run build       # Build optimized production bundle to web/dist
cd ..
```

### 4. Launch the Unified Full-Stack Sovereign Server
```bash
python server.py
# -> Open http://localhost:8090 (serves the Mizan React frontend + REST API + Law PDFs)
```
*Note: Pressing `Ctrl+C` cleanly shuts down the server with zero unhandled exceptions.*

---

## 📂 Project Structure

```text
moroccan-law-ai/
├── server.py                   # Full-Stack REST API + SQLite Audit Store + Static SPA Server (:8090)
├── data/
│   ├── gazette_offline_index.json # 13 Real Official Gazette (sgg.gov.ma) issues BO 7398–7542
│   ├── legal_audit.db          # SQLite persistent consultation & contract audit database
│   └── laws_pdf/               # Official Moroccan Law PDF Archive (24 files / 83.5 MB)
│       ├── manifest.json       # JSON manifest with checksums, dates, and SGG URLs
│       ├── ar/                 # Arabic editions (BO 5184, 5167, 5878, 4418, 5711, 6208...)
│       └── fr/                 # French editions (BO 5184, 5210, 5888, 4482, 5744, 6240...)
├── src/
│   ├── arabic_nlp.py           # Arabic normalization, Darija-to-statutory translator, domain classifier
│   ├── legal_rag.py            # Hybrid Okapi BM25 + Trigram Vector RRF (k=60) Legal RAG + Citation Safety
│   ├── bo_diff_engine.py       # Official Gazette (Jarida Rasmiya) article-by-article redline diff engine
│   ├── contract_auditor.py     # Moroccan Contract & Clause statutory compliance auditor
│   └── download_laws.py        # Official Moroccan Law PDF downloader & synchronization engine
├── tests/
│   ├── test_legal_rag.py       # Unit & safety verification tests for NLP and Hybrid RRF Legal RAG
│   ├── test_bo_diff_engine.py  # Unit tests for BO redline diffing and Contract Auditor
│   └── test_server.py          # Full-stack HTTP API tests for all REST endpoints & PDF resolution
├── wiki/                       # Comprehensive documentation & architectural specifications
│   ├── Home.md                 # Documentation portal
│   ├── 1-Architecture.md       # Technical architecture & RAG mathematics
│   ├── 2-Official-Laws-PDF-Archive.md # Moroccan Law PDF Archive catalogue & API
│   ├── 3-Darija-NLP-and-Statutory-Bridge.md # Darija/Arabizi lexical translation pipeline
│   ├── 4-Contract-Compliance-Auditor.md # Statutory nullity rules matrix
│   ├── 5-REST-API-Reference.md # Complete REST API documentation
│   └── Developer-Setup.md      # Development and contribution guide
└── web/                        # Bespoke Mizan React 19 + TypeScript + Vite + Tailwind Frontend
    ├── package.json
    ├── vite.config.ts          # Vite configuration with API proxy and Vitest setup
    ├── index.html              # HTML shell with BouazziMaghribi & IBM Plex Arabic fonts
    ├── public/fonts/           # Authentic Moroccan Maghribi calligraphy font
    └── src/
        ├── App.tsx             # Root application shell with tab router & language switcher
        ├── App.test.tsx        # Vitest suite covering navigation, i18n, redline, badges, dials
        ├── styles.css          # Tailwind CSS v4 styling & legal broadsheet chamber themes
        ├── lib/
        │   ├── types.ts        # TypeScript definitions for citations, audits, diffs, and BO issues
        │   ├── api.ts          # API client with AbortController support
        │   ├── i18n.ts         # Trilingual dictionary (Français, العربية, English)
        │   ├── redline.ts      # Word-level redline diffing utility
        │   └── cn.ts           # Classnames merger
        ├── components/
        │   ├── Logo.tsx        # Moroccan Mizan scale & geometric zellige octagon SVG
        │   ├── Shell.tsx       # Chamber layout shell
        │   ├── PageHeader.tsx  # Header with live health badge & language switcher
        │   ├── Redline.tsx     # Word-level redline renderer (<del> / <ins>)
        │   ├── RiskDial.tsx    # Animated SVG compliance risk gauge
        │   ├── SeverityBadge.tsx # High/Medium/Low compliance badges
        │   └── States.tsx      # Loading, error, and empty state visual cards
        └── views/
            ├── AskView.tsx     # Grounded legal consultation view with Darija tags
            ├── GazetteView.tsx # Bulletin Officiel issues browser & amendment inspector
            ├── CompareView.tsx # Side-by-side statutory diff comparator
            └── AuditView.tsx   # Contract compliance auditor with RiskDial gauge
```

---

## 📚 Documentation & Wiki

Detailed technical documentation, architectural specifications, and user manuals are available in the [`wiki/`](wiki/Home.md) directory:

1. [**Wiki Home & Platform Vision**](wiki/Home.md)
2. [**System Architecture & RAG Pipeline**](wiki/1-Architecture.md)
3. [**Official Moroccan Law PDF Archive (24 Codes)**](wiki/2-Official-Laws-PDF-Archive.md)
4. [**Darija & Arabizi Statutory Translation Bridge**](wiki/3-Darija-NLP-and-Statutory-Bridge.md)
5. [**Contract Compliance & Statutory Nullities Auditor**](wiki/4-Contract-Compliance-Auditor.md)
6. [**REST API Reference & Endpoints**](wiki/5-REST-API-Reference.md)
7. [**Developer Setup & Testing Guide**](wiki/Developer-Setup.md)

---

## 📄 License
[MIT](LICENSE) — © 2026 Oussama Elhadji (`@Bosaj`)
