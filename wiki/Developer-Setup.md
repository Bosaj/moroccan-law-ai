# Developer Setup & Testing Guide

## 1. Environment Requirements
- Python 3.10+ (tested through 3.14)
- Node.js 18+ (tested on Node 20+)
- npm 9+

---

## 2. Installation & Quickstart

### Step 1: Clone & Python Dependencies
```bash
git clone https://github.com/Bosaj/moroccan-law-ai.git
cd moroccan-law-ai

# Python standard library is used for zero-dependency backend!
# Optional: create a virtual environment
python -m venv .venv
# Windows: .venv\Scripts\activate
```

### Step 2: Download Official Moroccan Law PDFs (83.5 MB)
```bash
python src/download_laws.py
```

### Step 3: Install & Build React Frontend
```bash
cd web
npm install
npm test            # Run Vitest test suite (7 tests)
npm run typecheck   # Check TypeScript
npm run build       # Build production bundle to web/dist/
cd ..
```

### Step 4: Run the Sovereign Unified Server
```bash
python server.py
# -> Open http://localhost:8090
```

---

## 3. Automated Test Verification

### Backend Tests (13 tests)
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Frontend Tests (7 tests)
```bash
cd web
npm test
```
