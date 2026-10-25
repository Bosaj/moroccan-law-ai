"""
Moroccan Official Legal PDF Archive Downloader
Fetches authenticated, official Bulletin Officiel (BO / الجريدة الرسمية) legal PDFs
directly from the Moroccan General Secretariat of the Government (sgg.gov.ma).
Downloads bilingual collections (Arabic Edition Générale + French Traduction Officielle).
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.request
from typing import Dict, List, Optional

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data", "laws_pdf")
MANIFEST_PATH = os.path.join(DATA_DIR, "manifest.json")

# Master registry of Moroccan codes & statutory reforms with official SGG Bulletin Officiel URLs
MOROCCAN_OFFICIAL_LAWS = [
    {
        "id": "code_famille",
        "title_fr": "Code de la Famille (Moudawana)",
        "title_ar": "مدونة الأسرة",
        "law_number": "Loi n° 70-03",
        "dahir": "Dahir n° 1-04-22 du 12 hija 1424 (3 février 2004)",
        "domain": "family_law",
        "ar": {
            "bo_number": "BO 5184",
            "year": "2004",
            "date": "2004-02-05",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2004/BO_5184_Ar.pdf",
            "filename": "code_famille_moudawana_loi_70_03_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 5184",
            "year": "2004",
            "date": "2004-02-05",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2004/BO_5184_Fr.pdf",
            "filename": "code_famille_moudawana_loi_70_03_fr.pdf",
        },
    },
    {
        "id": "code_travail",
        "title_fr": "Code du Travail",
        "title_ar": "مدونة الشغل",
        "law_number": "Loi n° 65-99",
        "dahir": "Dahir n° 1-03-194 du 14 rejeb 1424 (11 septembre 2003)",
        "domain": "labor_law",
        "ar": {
            "bo_number": "BO 5167",
            "year": "2003",
            "date": "2003-12-08",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2003/BO_5167_Ar.pdf",
            "filename": "code_du_travail_loi_65_99_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 5210",
            "year": "2004",
            "date": "2004-05-06",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2004/BO_5210_Fr.pdf",
            "filename": "code_du_travail_loi_65_99_fr.pdf",
        },
    },
    {
        "id": "code_route",
        "title_fr": "Code de la Route (Loi 52-05)",
        "title_ar": "مدونة السير على الطرق",
        "law_number": "Loi n° 52-05",
        "dahir": "Dahir n° 1-10-07 du 26 safar 1431 (11 février 2010)",
        "domain": "traffic_law",
        "ar": {
            "bo_number": "BO 5878",
            "year": "2010",
            "date": "2010-09-30",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2010/BO_5878_Ar.pdf",
            "filename": "code_de_la_route_loi_52_05_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 5888",
            "year": "2010",
            "date": "2010-11-04",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2010/BO_5888_Fr.pdf",
            "filename": "code_de_la_route_loi_52_05_fr.pdf",
        },
    },
    {
        "id": "code_route_reforme",
        "title_fr": "Réforme du Code de la Route (Loi 116-14)",
        "title_ar": "تعديل وتتميم مدونة السير على الطرق",
        "law_number": "Loi n° 116-14",
        "dahir": "Dahir n° 1-16-106 du 13 kaada 1437 (17 août 2016)",
        "domain": "traffic_law",
        "ar": {
            "bo_number": "BO 6496",
            "year": "2016",
            "date": "2016-09-01",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2016/BO_6496_Ar.pdf",
            "filename": "reforme_code_route_loi_116_14_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 6496",
            "year": "2016",
            "date": "2016-09-01",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2016/BO_6496_Fr.pdf",
            "filename": "reforme_code_route_loi_116_14_fr.pdf",
        },
    },
    {
        "id": "code_commerce",
        "title_fr": "Code de Commerce & Sociétés Commerciales",
        "title_ar": "مدونة التجارة وقانون الشركات التجارية",
        "law_number": "Loi n° 15-95 & Loi n° 5-96",
        "dahir": "Dahir n° 1-96-83 du 15 rabii I 1417 (1er août 1996)",
        "domain": "commercial_law",
        "ar": {
            "bo_number": "BO 4418",
            "year": "1996",
            "date": "1996-10-03",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/1996/BO_4418_Ar.pdf",
            "filename": "code_de_commerce_loi_15_95_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 4482",
            "year": "1997",
            "date": "1997-05-15",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/1997/BO_4482_Fr.pdf",
            "filename": "code_de_commerce_loi_15_95_fr.pdf",
        },
    },
    {
        "id": "societes_anonymes",
        "title_fr": "Loi sur la Société Anonyme (SA)",
        "title_ar": "قانون شركة المساهمة",
        "law_number": "Loi n° 17-95",
        "dahir": "Dahir n° 1-96-124 du 14 rabii II 1417 (30 août 1996)",
        "domain": "corporate_law",
        "ar": {
            "bo_number": "BO 4422",
            "year": "1996",
            "date": "1996-10-17",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/1996/BO_4418_Ar.pdf",
            "filename": "societes_anonymes_loi_17_95_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 4418",
            "year": "1996",
            "date": "1996-10-03",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/1996/BO_4418_Fr.pdf",
            "filename": "societes_anonymes_loi_17_95_fr.pdf",
        },
    },
    {
        "id": "cndp_donnees_personnelles",
        "title_fr": "Protection des Données à Caractère Personnel (CNDP)",
        "title_ar": "حماية الأشخاص الذاتيين تجاه معالجة المعطيات ذات الطابع الشخصي",
        "law_number": "Loi n° 09-08",
        "dahir": "Dahir n° 1-09-15 du 22 safar 1430 (18 février 2009)",
        "domain": "data_protection",
        "ar": {
            "bo_number": "BO 5711",
            "year": "2009",
            "date": "2009-02-23",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2009/BO_5711_Ar.pdf",
            "filename": "loi_09_08_cndp_donnees_personnelles_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 5744",
            "year": "2009",
            "date": "2009-06-18",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2009/BO_5744_Fr.pdf",
            "filename": "loi_09_08_cndp_donnees_personnelles_fr.pdf",
        },
    },
    {
        "id": "baux_habitation",
        "title_fr": "Baux d'Habitation et à Usage Professionnel",
        "title_ar": "الكراء السكني والاستعمال المهني",
        "law_number": "Loi n° 67-12",
        "dahir": "Dahir n° 1-13-111 du 15 moharrem 1435 (19 novembre 2013)",
        "domain": "real_estate_lease",
        "ar": {
            "bo_number": "BO 6208",
            "year": "2013",
            "date": "2013-11-28",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2013/BO_6208_Ar.pdf",
            "filename": "loi_67_12_baux_habitation_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 6240",
            "year": "2014",
            "date": "2014-03-20",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2014/BO_6240_Fr.pdf",
            "filename": "loi_67_12_baux_habitation_fr.pdf",
        },
    },
    {
        "id": "droits_reels",
        "title_fr": "Code des Droits Réels",
        "title_ar": "مدونة الحقوق العينية",
        "law_number": "Loi n° 39-08",
        "dahir": "Dahir n° 1-11-178 du 25 hija 1432 (22 novembre 2011)",
        "domain": "property_law",
        "ar": {
            "bo_number": "BO 5998",
            "year": "2011",
            "date": "2011-11-24",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2011/BO_5998_Ar.pdf",
            "filename": "code_des_droits_reels_loi_39_08_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 6022",
            "year": "2012",
            "date": "2012-02-16",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2012/BO_6022_Fr.pdf",
            "filename": "code_des_droits_reels_loi_39_08_fr.pdf",
        },
    },
    {
        "id": "protection_consommateur",
        "title_fr": "Protection du Consommateur",
        "title_ar": "تدابير حماية المستهلك",
        "law_number": "Loi n° 31-08",
        "dahir": "Dahir n° 1-11-03 du 14 rabii I 1432 (18 février 2011)",
        "domain": "consumer_law",
        "ar": {
            "bo_number": "BO 5932",
            "year": "2011",
            "date": "2011-04-07",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2011/BO_5932_Ar.pdf",
            "filename": "protection_consommateur_loi_31_08_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 5932",
            "year": "2011",
            "date": "2011-04-07",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2011/BO_5932_Fr.pdf",
            "filename": "protection_consommateur_loi_31_08_fr.pdf",
        },
    },
    {
        "id": "violence_femmes",
        "title_fr": "Lutte contre les Violences faites aux Femmes (Code Pénal)",
        "title_ar": "محاربة العنف ضد النساء وتعديل القانون الجنائي",
        "law_number": "Loi n° 103-13",
        "dahir": "Dahir n° 1-18-19 du 5 joumada II 1439 (22 février 2018)",
        "domain": "criminal_law",
        "ar": {
            "bo_number": "BO 6655",
            "year": "2018",
            "date": "2018-03-12",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2018/BO_6655_Ar.pdf",
            "filename": "loi_103_13_violence_femmes_code_penal_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 6706",
            "year": "2018",
            "date": "2018-09-06",
            "url": "https://www.sgg.gov.ma/BO/bo_fr/2018/BO_6706_Fr.pdf",
            "filename": "loi_103_13_violence_femmes_code_penal_fr.pdf",
        },
    },
    {
        "id": "reforme_societes_sas",
        "title_fr": "Modernisation des Sociétés Commerciales & SAS Simplifiée",
        "title_ar": "تحديث قانون الشركات وتيسير شركة المساهمة المبسطة",
        "law_number": "Loi n° 19-20 & Loi n° 20-19",
        "dahir": "Dahir n° 1-21-75 du 3 hija 1442 (14 juillet 2021)",
        "domain": "corporate_law",
        "ar": {
            "bo_number": "BO 6975",
            "year": "2021",
            "date": "2021-07-26",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2021/BO_6975_Ar.pdf",
            "filename": "reforme_societes_commerciales_loi_19_20_ar.pdf",
        },
        "fr": {
            "bo_number": "BO 7010",
            "year": "2021",
            "date": "2021-08-16",
            "url": "https://www.sgg.gov.ma/BO/bo_ar/2021/BO_6975_Ar.pdf",
            "filename": "reforme_societes_commerciales_loi_19_20_fr.pdf",
        },
    },
]


def create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def download_file(url: str, dest_path: str, max_retries: int = 3) -> bool:
    """Downloads a file with SSL bypass, user-agent headers, and retry logic."""
    if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 10_000:
        return True  # Already cached

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    temp_path = dest_path + ".part"

    ctx = create_ssl_context()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.sgg.gov.ma/",
        },
    )

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=25) as resp:
                if resp.status != 200:
                    continue
                with open(temp_path, "wb") as f:
                    while chunk := resp.read(64 * 1024):
                        f.write(chunk)
            
            if os.path.getsize(temp_path) > 500:
                os.replace(temp_path, dest_path)
                return True
        except Exception as exc:
            if attempt == max_retries:
                print(f"[ERROR] Failed to download {url}: {exc}")
            time.sleep(1)

    if os.path.exists(temp_path):
        os.remove(temp_path)
    return False


def sync_all_laws() -> dict:
    """Downloads all Moroccan legal codes (Arabic & French) and saves the index manifest."""
    os.makedirs(os.path.join(DATA_DIR, "ar"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "fr"), exist_ok=True)

    manifest_entries = []
    total_downloaded = 0
    total_bytes = 0

    print("==================================================================")
    print("[Mizan] SYNCHRONIZING MOROCCAN OFFICIAL LEGAL PDF ARCHIVE (SGG.GOV.MA)")
    print("==================================================================")

    for item in MOROCCAN_OFFICIAL_LAWS:
        law_id = item["id"]
        title_fr = item["title_fr"]
        title_ar = item["title_ar"]

        entry = {
            "id": law_id,
            "title_fr": title_fr,
            "title_ar": title_ar,
            "law_number": item["law_number"],
            "dahir": item["dahir"],
            "domain": item["domain"],
            "files": {},
        }

        # Arabic edition
        ar_info = item["ar"]
        ar_dest = os.path.join(DATA_DIR, "ar", ar_info["filename"])
        print(f"📥 [{law_id}] Arabic: {ar_info['bo_number']} ({title_ar})...", end=" ", flush=True)
        ok_ar = download_file(ar_info["url"], ar_dest)
        if ok_ar and os.path.isfile(ar_dest):
            sz = os.path.getsize(ar_dest)
            total_bytes += sz
            total_downloaded += 1
            print(f"DONE ({sz / (1024*1024):.2f} MB)")
            entry["files"]["ar"] = {
                "bo_number": ar_info["bo_number"],
                "publication_date": ar_info["date"],
                "local_path": f"data/laws_pdf/ar/{ar_info['filename']}",
                "size_bytes": sz,
                "url": ar_info["url"],
            }
        else:
            print("FAILED")

        # French edition
        fr_info = item["fr"]
        fr_dest = os.path.join(DATA_DIR, "fr", fr_info["filename"])
        print(f"📥 [{law_id}] French: {fr_info['bo_number']} ({title_fr})...", end=" ", flush=True)
        ok_fr = download_file(fr_info["url"], fr_dest)
        if ok_fr and os.path.isfile(fr_dest):
            sz = os.path.getsize(fr_dest)
            total_bytes += sz
            total_downloaded += 1
            print(f"DONE ({sz / (1024*1024):.2f} MB)")
            entry["files"]["fr"] = {
                "bo_number": fr_info["bo_number"],
                "publication_date": fr_info["date"],
                "local_path": f"data/laws_pdf/fr/{fr_info['filename']}",
                "size_bytes": sz,
                "url": fr_info["url"],
            }
        else:
            print("FAILED")

        manifest_entries.append(entry)

    manifest = {
        "institution": "Secrétariat Général du Gouvernement (Royaume du Maroc — sgg.gov.ma)",
        "source": "Official Gazette (Bulletin Officiel — الجريدة الرسمية)",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_laws_count": len(manifest_entries),
        "total_files_downloaded": total_downloaded,
        "total_archive_size_mb": round(total_bytes / (1024 * 1024), 2),
        "laws": manifest_entries,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print("==================================================================")
    print(f"[OK] Archive complete: {total_downloaded} files saved, {manifest['total_archive_size_mb']} MB")
    print(f"[OK] Manifest written to: {MANIFEST_PATH}")
    print("==================================================================")
    return manifest


def get_law_manifest() -> dict:
    if os.path.isfile(MANIFEST_PATH):
        try:
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return sync_all_laws()


if __name__ == "__main__":
    sync_all_laws()
