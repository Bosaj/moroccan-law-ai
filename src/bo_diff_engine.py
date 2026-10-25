"""
Bulletin Officiel (الجريدة الرسمية — Jarida Rasmiya) Redline Diff & Compliance Alert Engine (#17)
Integrates:
- Word-by-word and clause-level statutory redline diffing (`compute_article_redline_diff`)
- Compliance severity classification (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
- Curated legislative redlines + 13 real Moroccan Official Gazette (`sgg.gov.ma`) issues
  from `data/gazette_offline_index.json` (ported from `gazette-digest`) with trilingual summaries
  (French, Arabic MSA, and Moroccan Darija).
"""

import difflib
import json
import os
from typing import Any, Dict, List, Optional


class BulletinOfficielDiffEngine:
    """Computes article-level redline diffs and compliance alerts for Moroccan laws."""

    HIGH_IMPACT_KEYWORDS = [
        "amende", "emprisonnement", "pénalité", "nullité", "obligatoire", "interdit",
        "délai", "capital", "indemnité", "cotisation", "impôt", "taxe", "cndp", "dirhams",
        "غرامة", "حبس", "عقوبة", "بطلان", "إلزامي", "يمنع", "أجل", "رأسمال", "تعويض", "ضريبة", "درهم",
    ]

    @classmethod
    def compute_article_redline_diff(
        cls,
        old_text: str,
        new_text: str,
        article_ref: str = "Article",
        bo_issue: str = "BO",
    ) -> Dict[str, Any]:
        old_words = old_text.split()
        new_words = new_text.split()

        matcher = difflib.SequenceMatcher(None, old_words, new_words)
        added_tokens: List[str] = []
        removed_tokens: List[str] = []
        html_parts: List[str] = []
        md_parts: List[str] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                segment = " ".join(old_words[i1:i2])
                html_parts.append(segment)
                md_parts.append(segment)
            elif tag == "delete":
                removed = " ".join(old_words[i1:i2])
                removed_tokens.extend(old_words[i1:i2])
                html_parts.append(
                    f'<del style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:4px;text-decoration:line-through;">{removed}</del>'
                )
                md_parts.append(f"[-{removed}-]")
            elif tag == "insert":
                added = " ".join(new_words[j1:j2])
                added_tokens.extend(new_words[j1:j2])
                html_parts.append(
                    f'<ins style="background:#064e3b;color:#6ee7b7;padding:1px 5px;border-radius:4px;text-decoration:none;font-weight:600;">{added}</ins>'
                )
                md_parts.append(f"{{+{added}+}}")
            elif tag == "replace":
                removed = " ".join(old_words[i1:i2])
                added = " ".join(new_words[j1:j2])
                removed_tokens.extend(old_words[i1:i2])
                added_tokens.extend(new_words[j1:j2])
                html_parts.append(
                    f'<del style="background:#450a0a;color:#fca5a5;padding:1px 5px;border-radius:4px;text-decoration:line-through;">{removed}</del> '
                    f'<ins style="background:#064e3b;color:#6ee7b7;padding:1px 5px;border-radius:4px;text-decoration:none;font-weight:600;">{added}</ins>'
                )
                md_parts.append(f"[-{removed}-] {{+{added}+}}")

        similarity = matcher.ratio()
        change_ratio = round(1.0 - similarity, 4)

        combined_changed = " ".join(added_tokens + removed_tokens).lower()
        has_high_impact_kw = any(kw in combined_changed for kw in cls.HIGH_IMPACT_KEYWORDS)

        if change_ratio >= 0.35 and has_high_impact_kw:
            severity = "CRITICAL"
        elif change_ratio >= 0.15 or has_high_impact_kw:
            severity = "HIGH"
        elif change_ratio >= 0.05:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "article_ref": article_ref,
            "bo_issue": bo_issue,
            "old_text": old_text,
            "new_text": new_text,
            "added_tokens": added_tokens,
            "removed_tokens": removed_tokens,
            "change_ratio": change_ratio,
            "similarity_ratio": round(similarity, 4),
            "compliance_severity": severity,
            "redline_html": " ".join(html_parts),
            "redline_markdown": " ".join(md_parts),
        }

    def __init__(self) -> None:
        self._issues = self._build_curated_bo_issues()

    def _build_curated_bo_issues(self) -> List[Dict[str, Any]]:
        raw_issues: List[Dict[str, Any]] = [
            {
                "bo_number": "BO n° 7213",
                "edition": "Édition Générale (النشرة العامة)",
                "publication_date": "2023-07-17",
                "title_ar": "القانون رقم 69.21 بتغيير القانون رقم 15.95 المتعلق بمدونة التجارة (آجال الأداء والغرامات المالية)",
                "title_fr": "Loi n° 69-21 modifiant la Loi n° 15-95 formant Code de Commerce (Délais de paiement & sanctions pécuniaires)",
                "source_url": "https://www.sgg.gov.ma/BulletinOfficiel.aspx",
                "target_audience": ["Accountants", "SMEs", "Corporate Lawyers"],
                "target_audiences": ["Accountants", "SMEs", "Corporate Lawyers"],
                "amendments": [
                    {
                        "code": "Code de Commerce (مدونة التجارة)",
                        "article_ref": "Article 78-2 (Loi n° 69-21)",
                        "old_text": (
                            "Article 78-2 : Le délai de paiement des sommes dues est fixé au soixantième jour "
                            "suivant la date de réception des marchandises ou d'exécution de la prestation, "
                            "sans déclaration trimestrielle électronique obligatoire à la DGI."
                        ),
                        "new_text": (
                            "Article 78-2 : Le délai de paiement est fixé à 60 jours à compter de la date de "
                            "facturation (ou 120 jours max par accord), avec déclaration trimestrielle électronique "
                            "obligatoire auprès de la DGI et amende pécuniaire proportionnelle au taux directeur de Bank Al-Maghrib."
                        ),
                        "summary_ar": "تحديد أجل الأداء بين المقاولات في 60 يوماً من تاريخ الفوترة (أو 120 يوماً كحد أقصى باتفاق الطرفين) مع إجبارية التصريح الإلكتروني كل ثلاثة أشهر لدى المديرية العامة للضرائب (DGI) تحت طائلة غرامات مالية.",
                        "summary_fr": "Plafonnement des délais de paiement inter-entreprises à 60 jours (120 jours max par convention) à compter de la facturation, assorti d'une déclaration trimestrielle obligatoire à la DGI et de sanctions pécuniaires.",
                        "summary_darija": "الشركات والمقاولات ولاو ملزمين يخلصو الفواتير داخل أجل 60 يوم (أو 120 يوم على الأكثر إلا كان اتفاق مكتوب)، ويديرو تصريح إلكتروني كل 3 شهور عند الضرائب (DGI) وإلا غيتعرضو لغرامة مالية.",
                    }
                ],
            },
            {
                "bo_number": "BO n° 7006",
                "edition": "Édition Générale (النشرة العامة)",
                "publication_date": "2021-07-22",
                "title_ar": "القانون رقم 19.20 بتغيير وتتميم القانون رقم 5.96 المتعلق بشركات التضامن والشركات ذات المسؤولية المحدودة (SARL)",
                "title_fr": "Loi n° 19-20 modifiant et complétant la Loi n° 5-96 sur la SARL et les sociétés commerciales",
                "source_url": "https://www.sgg.gov.ma/BulletinOfficiel.aspx",
                "target_audience": ["Corporate Lawyers", "Accountants", "SMEs"],
                "target_audiences": ["Corporate Lawyers", "Accountants", "SMEs"],
                "amendments": [
                    {
                        "code": "Loi n° 5-96 sur la SARL",
                        "article_ref": "Articles 46 & 71 (Gouvernance & Assemblées à distance)",
                        "old_text": (
                            "Article 71 : Les associés doivent se réunir physiquement au siège social pour "
                            "délibérer en assemblée générale sans possibilité de vote par visioconférence pour les décisions statutaires."
                        ),
                        "new_text": (
                            "Article 71 : Sont réputés présents pour le calcul du quorum et de la majorité les associés "
                            "qui participent à l'assemblée générale par des moyens de visioconférence ou par tout moyen équivalent permettant leur identification."
                        ),
                        "summary_ar": "السماح رسمياً للشركاء في الشركات ذات المسؤولية المحدودة (SARL) بعقد الجموع العامة والتصويت عن بُعد عبر تقنيات التناظر المرئي (Visioconférence).",
                        "summary_fr": "Autorisation légale de tenir les assemblées générales de SARL et de calculer le quorum/majorité par visioconférence.",
                        "summary_darija": "الشركاء في شركة SARL ولا عندهم الحق قانونياً يديرو الاجتماعات والجموع العامة ويصوتو عن بُعد بـ الفيديو (Visioconférence) بلا ما يحضرو جسدياً للمقر.",
                    }
                ],
            },
            {
                "bo_number": "BO n° 6948",
                "edition": "Édition Générale (النشرة العامة)",
                "publication_date": "2020-12-31",
                "title_ar": "القانون رقم 43.20 المتعلق بخدمات الثقة بشأن المعاملات الإلكترونية (التوقيع والخاتم الإلكتروني)",
                "title_fr": "Loi n° 43-20 relative aux services de confiance pour les transactions électroniques",
                "source_url": "https://www.sgg.gov.ma/BulletinOfficiel.aspx",
                "target_audience": ["Tech Startups", "DPOs", "Lawyers"],
                "target_audiences": ["Tech Startups", "DPOs", "Lawyers"],
                "amendments": [
                    {
                        "code": "Loi n° 43-20 (remplaçant les dispositions de la Loi n° 53-05)",
                        "article_ref": "Articles 5, 6 & 20",
                        "old_text": (
                            "Loi 53-05 : Seule la signature électronique sécurisée reposant sur un certificat "
                            "délivré par un prestataire agréé possède une valeur probante reconnue."
                        ),
                        "new_text": (
                            "Loi 43-20 : Instaure trois niveaux de signature électronique (simple, avancée et qualifiée), "
                            "le cachet électronique d'entreprise et l'horodatage électronique qualifié sous le contrôle de la DGSSI."
                        ),
                        "summary_ar": "إحداث ثلاثة مستويات للتوقيع الإلكتروني (البسيط، المتقدم، والمؤهل) واعتماد الخاتم الإلكتروني للمقاولات والختم الزمني تحت إشراف المديرية العامة لأمن نظم المعلومات (DGSSI).",
                        "summary_fr": "Introduction de 3 niveaux de signature électronique (simple, avancée, qualifiée), du cachet électronique pour les personnes morales et de l'horodatage sous l'autorité de la DGSSI.",
                        "summary_darija": "القانون 43.20 نظم التوقيع الإلكتروني فالمغرب على 3 درجات (بسيط، متقدم، ومؤهل) وزاد الكاشي الإلكتروني ديال الشركات (Cachet électronique) باش العقود الرقمية تكون مقبولة قانونياً فالمحاكم.",
                    }
                ],
            },
            {
                "bo_number": "BO n° 6970",
                "edition": "Édition Générale (النشرة العامة)",
                "publication_date": "2021-03-18",
                "title_ar": "القانون رقم 15.18 المتعلق بالتمويل التعاوني (Crowdfunding بالمغرب)",
                "title_fr": "Loi n° 15-18 relative au financement collaboratif (Crowdfunding)",
                "source_url": "https://www.sgg.gov.ma/BulletinOfficiel.aspx",
                "target_audience": ["Tech Startups", "SMEs", "Corporate Lawyers"],
                "target_audiences": ["Tech Startups", "SMEs", "Corporate Lawyers"],
                "amendments": [
                    {
                        "code": "Dahir n° 1-21-24 / Loi n° 15-18",
                        "article_ref": "Articles 1, 4 & 12",
                        "old_text": (
                            "Collecte publique de fonds pour des projets entrepreneuriaux ou associatifs non encadrée "
                            "par un statut spécifique de société de financement collaboratif."
                        ),
                        "new_text": (
                            "Loi 15-18 : Encadre légalement le financement collaboratif sous trois formes (prêt, "
                            "investissement en capital et don) via des plateformes (SFC) agréées par Bank Al-Maghrib et l'AMMC."
                        ),
                        "summary_ar": "تقنين التمويل التعاوني (Crowdfunding) في المغرب عبر ثلاث صيغ (الاستثمار في رأس المال، القرض، والتبرع) تحت رقابة بنك المغرب والهيئة المغربية لسوق الرساميل (AMMC).",
                        "summary_fr": "Création du cadre légal marocain du Crowdfunding (investissement, prêt et don) supervisé par Bank Al-Maghrib et l'AMMC.",
                        "summary_darija": "منصات التمويل التعاوني (Crowdfunding) ولات مقننة رسمياً فالمغرب تحت مراقبة بنك المغرب وAMMC باش المقاولات الناشئة (Startups) والجمعيات يقدرو يجمعو التمويل بطريقة قانونية.",
                    }
                ],
            },
        ]

        # Also load the 13 real Official Gazette issues from data/gazette_offline_index.json
        offline_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "gazette_offline_index.json"
        )
        if os.path.isfile(offline_path):
            try:
                with open(offline_path, "r", encoding="utf-8") as f:
                    offline_data = json.load(f)
                for bo_num, item in offline_data.items():
                    entries = item.get("entries", [])
                    if not entries:
                        continue
                    first_entry = entries[0]
                    cat = first_entry.get("category", "Loi")
                    audiences = (
                        ["SMEs", "Tech Startups", "Citizens", "Lawyers"]
                        if cat == "Loi"
                        else ["HR", "Citizens", "Lawyers"]
                    )
                    # The offline index only carries summaries of what each gazette entry
                    # publishes. It does NOT contain the superseded article text, so no
                    # old_text / redline is fabricated for these entries.
                    amendments = []
                    for ent in entries:
                        amendments.append(
                            {
                                "code": f"Bulletin Officiel ({cat})",
                                "article_ref": f"{cat} — Page {ent.get('source_page_start', 1)}",
                                "provenance": "gazette_index_summary",
                                "old_text": None,
                                "new_text": None,
                                "summary_ar": ent.get("summary_ar", ""),
                                "summary_fr": ent.get("summary_fr", ""),
                                "summary_darija": ent.get("summary_darija", ""),
                                "redline_diff": None,
                            }
                        )
                    raw_issues.append(
                        {
                            "bo_number": f"BO n° {bo_num}",
                            "edition": "Édition Générale (الأمانة العامة للحكومة)",
                            "publication_date": item.get("publication_date", "2026-01-01"),
                            "title_ar": first_entry.get("title_ar", f"الجريدة الرسمية عدد {bo_num}"),
                            "title_fr": first_entry.get("title_fr", f"Bulletin Officiel n° {bo_num}"),
                            "source_url": item.get(
                                "source_url", "https://www.sgg.gov.ma/BulletinOfficiel.aspx"
                            ),
                            "total_pages": item.get("total_pages", 32),
                            "target_audience": audiences,
                            "target_audiences": audiences,
                            "amendments": amendments,
                        }
                    )
            except Exception:
                pass

        for issue in raw_issues:
            for am in issue["amendments"]:
                if am.get("old_text") is None or am.get("new_text") is None:
                    continue
                # Curated entries are hand-written paraphrases for demonstration, not
                # verbatim Bulletin Officiel text; the API says so explicitly.
                am.setdefault("provenance", "curated_paraphrase")
                am["redline_diff"] = self.compute_article_redline_diff(
                    old_text=am["old_text"],
                    new_text=am["new_text"],
                    article_ref=am["article_ref"],
                    bo_issue=issue["bo_number"],
                )
        return raw_issues

    def list_bo_issues(
        self,
        audience: Optional[str] = None,
        audience_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        selected = audience or audience_filter
        if not selected or selected.lower() == "all":
            return self._issues
        return [
            iss
            for iss in self._issues
            if any(selected.lower() in aud.lower() for aud in iss.get("target_audiences", []))
        ]
