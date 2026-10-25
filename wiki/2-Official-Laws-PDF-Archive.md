# 2. Official Moroccan Laws PDF Archive

## 2.1 Overview & SGG Provenance

Under Moroccan constitutional law, statutory texts acquire binding legal force upon publication in the **Official Gazette (*Bulletin Officiel* — الجrيدة الرسمية)**, published by the **Secrétariat Général du Gouvernement (`sgg.gov.ma`)**.

The **Mizan Official Legal PDF Archive** (`src/download_laws.py`) is an automated, sovereign synchronization tool that downloads, verifies, and stores the official PDF issues of Moroccan legislation in both:
1. **Édition Générale (Arabic):** The authoritative original Arabic enactment.
2. **Édition de Traduction Officielle (French):** The official state French translation.

## 2.2 Catalog of Synchronized Moroccan Codes (24 Official PDFs / 83.5 MB)

All files are stored in `data/laws_pdf/ar/` and `data/laws_pdf/fr/`:

| Law Code | Law Number | Royal Dahir | Arabic Edition (SGG) | French Translation (SGG) |
|:---|:---|:---|:---|:---|
| **Code de la Famille (Moudawana)** | Loi n° 70-03 | Dahir 1-04-22 (3 fév 2004) | `BO 5184` (1.61 MB) | `BO 5184` (5.48 MB) |
| **Code du Travail** | Loi n° 65-99 | Dahir 1-03-194 (11 sept 2003) | `BO 5167` (5.82 MB) | `BO 5210` (10.67 MB) |
| **Code de la Route** | Loi n° 52-05 | Dahir 1-10-07 (11 fév 2010) | `BO 5878` (5.05 MB) | `BO 5888` (3.33 MB) |
| **Réforme Code de la Route** | Loi n° 116-14 | Dahir 1-16-106 (17 août 2016) | `BO 6496` (2.49 MB) | `BO 6496` (1.72 MB) |
| **Code de Commerce** | Loi n° 15-95 | Dahir 1-96-83 (1er août 1996) | `BO 4418` (2.82 MB) | `BO 4482` (3.53 MB) |
| **Sociétés Anonymes (SA)** | Loi n° 17-95 | Dahir 1-96-124 (30 août 1996) | `BO 4422` (2.82 MB) | `BO 4418` (6.57 MB) |
| **Données Personnelles (CNDP)** | Loi n° 09-08 | Dahir 1-09-15 (18 fév 2009) | `BO 5711` (0.50 MB) | `BO 5744` (4.95 MB) |
| **Baux d'Habitation** | Loi n° 67-12 | Dahir 1-13-111 (19 nov 2013) | `BO 6208` (1.15 MB) | `BO 6240` (4.84 MB) |
| **Code des Droits Réels** | Loi n° 39-08 | Dahir 1-11-178 (22 nov 2011) | `BO 5998` (2.93 MB) | `BO 6022` (3.21 MB) |
| **Protection Consommateur** | Loi n° 31-08 | Dahir 1-11-03 (18 fév 2011) | `BO 5932` (2.12 MB) | `BO 5932` (3.72 MB) |
| **Violences Faites aux Femmes** | Loi n° 103-13 | Dahir 1-18-19 (22 fév 2018) | `BO 6655` (3.34 MB) | `BO 6706` (3.52 MB) |
| **Sociétés Commerciales & SAS** | Loi n° 19-20 | Dahir 1-21-75 (14 juil 2021) | `BO 6975` (0.67 MB) | `BO 7010` (0.67 MB) |

## 2.3 Automated Sync & Verification Script

To re-synchronize or update the archive at any time:
```bash
python src/download_laws.py
```
This utility:
- Verifies SSL certificates with resilient fallback.
- Detects existing cached files (`>10 KB`) to prevent redundant bandwidth consumption.
- Generates `data/laws_pdf/manifest.json` indexing file sizes, checksums, and publication metadata.

## 2.4 HTTP API Access

The full-stack web server exposes:
- **`GET /api/laws-pdf`**: Returns the complete JSON manifest of available laws.
- **`GET /data/laws_pdf/ar/{filename}`**: Streams the Arabic edition PDF directly with correct `Content-Type: application/pdf` and cache headers.
- **`GET /data/laws_pdf/fr/{filename}`**: Streams the French edition PDF directly.
