# Welcome to the Mizan (ميزان) Wiki · Moroccan Law AI & BO Redline Engine

Welcome to the official documentation and technical wiki for **Mizan** (`@Bosaj/moroccan-law-ai`).

---

## ⚖️ Project Vision

**Mizan (ميزان)** is a sovereign Moroccan legal technology platform unifying grounded statutory question answering, an automated **Official Gazette (*Bulletin Officiel* — الجريدة الرسمية `sgg.gov.ma`)** article-by-article redline diff engine, an automated Moroccan contract compliance auditor, and a comprehensive bilingual archive of official Moroccan law PDFs.

### Key Tenets
1. **Source-Grounded Statutory Truth:** Strict separation between verbatim Moroccan law (citing exact Dahir, Law Number, Bulletin Officiel issue, publication date, and article number) and plain-language commentary.
2. **Moroccan Darija & Arabizi Inclusion:** Citizens can ask questions in everyday spoken Moroccan Darija (in Arabic or Latin Arabizi scripts) and receive answers grounded in formal Moroccan legislation.
3. **Sovereign Legal Design:** Bespoke React 19 frontend (*Mizan* · ميزان) with authentic Maghribi calligraphy (`Bouazzi Maghribi`), bidirectional RTL mirroring, and an octagonal zellige scale brand mark.
4. **Official Legal PDF Archive:** Automated synchronization engine pulling real, official *Bulletin Officiel* PDFs directly from `sgg.gov.ma` in both Arabic (Edition Générale) and French (Traduction Officielle).

---

## 📑 Wiki Documentation Index

1. **[System Architecture & Tech Stack](1-Architecture.md)**  
   *Full-stack architecture, Hybrid Okapi BM25 + Trigram Vector RRF (k=60), anti-hallucination verification gate, and React 19 SPA design.*

2. **[Official Moroccan Law PDF Archive](2-Official-Laws-PDF-Archive.md)**  
   *Catalogue of 24 real official Moroccan law PDFs (Arabic & French) downloaded from sgg.gov.ma, synchronization engine, and API access.*

3. **[Moroccan Darija NLP & Statutory Translation Bridge](3-Darija-NLP-and-Statutory-Bridge.md)**  
   *Linguistic pipeline converting everyday Moroccan Darija and Arabizi into formal statutory search terms across labor, family, lease, and commercial codes.*

4. **[Moroccan Contract Compliance Auditor](4-Contract-Compliance-Auditor.md)**  
   *Statutory nullity detection rulebook under Moroccan law (excessive probation periods, advance severance waivers, undeclared biometric processing).*

5. **[REST API Reference & Endpoints](5-REST-API-Reference.md)**  
   *Specification of `/api/health`, `/api/query`, `/api/bo-issues`, `/api/bo-diff`, `/api/audit-contract`, and `/api/laws-pdf`.*

6. **[Developer Setup & Testing](Developer-Setup.md)**  
   *Instructions for local Python environment, Node.js React client, running test suites, and production deployment.*

---
*Maintained by Oussama EL HADJI ([@Bosaj](https://github.com/Bosaj)) — `oussousselhadji@gmail.com`.*
