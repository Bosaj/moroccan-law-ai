# ⚖️ Mizan (ميزان) — Moroccan Law AI + Official Gazette (*Jarida Rasmiya*) Redline Engine

> **Unified Moroccan Legal Tech Platform (Master Dossier Ideas #07 + #17):** Grounded Moroccan Statutory Q&A in **Arabic (MSA)**, **Français**, and **Moroccan Darija** (Arabic & Arabizi scripts), paired with an **Official Gazette (*Bulletin Officiel* — الجريدة الرسمية `sgg.gov.ma`) Article-by-Article Redline Diff & Compliance Alert Engine** and a **Moroccan Contract Compliance Auditor**. Powered by a bespoke, high-performance **React 19 + TypeScript + Vite + Tailwind CSS** frontend (*Mizan* · ميزان).

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

### 5. Production-Grade Trilingual React Frontend (*Mizan* · ميزان) (`web/`)
- Bespoke Moroccan sovereign legal design system:
  - Authentic Moroccan Maghribi calligraphy (`BouazziMaghribi`) for headers and royal Dahir seals.
  - IBM Plex Sans Arabic for crisp legal typography in Modern Standard Arabic with full bidirectional RTL mirroring (`dir="rtl"`).
  - Warm charcoal & brass chamber palette with double-bezel borders and gold accents (`#d97706`, `#b45309`).
  - Interactive tabs:
    1. **Consultation Juridique:** Real-time Moroccan legal Q&A with Darija translation badges, verbatim bilingual statutory citations, and plain-language commentary.
    2. **Veille Bulletin Officiel:** Searchable database of 18 BO issues with audience filtering and article amendment breakdowns.
    3. **Comparateur de Réformes:** Side-by-side legal text comparator with word-level redline diffs and token-level change metrics.
    4. **Audit de Contrats:** Paste any Moroccan contract for instant compliance scoring, RiskDial SVG gauge, flagged illegal clauses, and actionable remediation steps.

---

## 🚀 Quickstart

### 1. Run Automated Unit & API Tests (Python Backend)
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 2. Frontend Development & Build (`web/`)
```bash
cd web
npm install
npm test            # Run Vitest test suite
npm run typecheck   # Typecheck with TypeScript
npm run build       # Build optimized production bundle to web/dist
```

### 3. Launch the Unified Full-Stack Sovereign Server
```bash
python server.py
# -> Open http://localhost:8090 (serves the Mizan React frontend + REST API)
```

For hot-reload frontend development:
```bash
# Terminal 1: Backend API
python server.py

# Terminal 2: Vite Dev Server with proxy to :8090
cd web
npm run dev
# -> Open http://localhost:5174
```

---

## 📂 Project Structure

```text
moroccan-law-ai/
├── server.py                   # Full-Stack REST API + SQLite Audit Store + Static SPA Server (:8090)
├── data/
│   ├── gazette_offline_index.json # 13 Real Official Gazette (sgg.gov.ma) issues BO 7398–7542
│   └── legal_audit.db          # SQLite persistent consultation & contract audit database
├── src/
│   ├── arabic_nlp.py           # Arabic normalization, Darija-to-statutory translator, domain classifier
│   ├── legal_rag.py            # Hybrid Okapi BM25 + Trigram Vector RRF (k=60) Legal RAG + Citation Safety
│   ├── bo_diff_engine.py       # Official Gazette (Jarida Rasmiya) article-by-article redline diff engine
│   └── contract_auditor.py     # Moroccan Contract & Clause statutory compliance auditor
├── tests/
│   ├── test_legal_rag.py       # Unit & safety verification tests for NLP and Hybrid RRF Legal RAG
│   ├── test_bo_diff_engine.py  # Unit tests for BO redline diffing and Contract Auditor
│   └── test_server.py          # Full-stack HTTP API tests for all REST endpoints
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

## 📄 License
[MIT](LICENSE) — © 2026 Oussama Elhadji (`@Bosaj`)
