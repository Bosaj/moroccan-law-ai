"""
Moroccan Law AI & Official Gazette (Jarida Rasmiya) Redline Engine
Unified Master Dossier Architecture (Ideas #07 + #17)
Trilingual (Arabic MSA / Français / Moroccan Darija) with Strict Citation Safety
"""

import streamlit as st
from src.arabic_nlp import MoroccanLegalNLP
from src.bo_diff_engine import BulletinOfficielDiffEngine
from src.contract_auditor import MoroccanContractAuditor
from src.legal_rag import MoroccanLegalRAG

st.set_page_config(
    page_title="Moroccan Law AI & BO Redline Engine | المساعد القانوني المغربي والجريدة الرسمية",
    page_icon="⚖️",
    layout="wide",
)

# Custom styling for verbatim vs AI commentary cards and BO redline diffs
st.markdown(
    """
    <style>
    .verbatim-box {
        background: #0f172a;
        border-left: 5px solid #d4af37;
        padding: 16px;
        border-radius: 10px;
        color: #f8fafc;
        margin-bottom: 12px;
    }
    .commentary-box {
        background: #1e293b;
        border-left: 5px solid #38bdf8;
        padding: 16px;
        border-radius: 10px;
        color: #e2e8f0;
        margin-bottom: 12px;
    }
    .verified-badge {
        display: inline-block;
        background: #065f46;
        color: #a7f3d0;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 0.82rem;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("⚖️ Moroccan Law AI + Bulletin Officiel Redline Engine")
st.caption(
    "المساعد القانوني المغربي الذكي ومحرك تتبع تعديلات الجريدة الرسمية (الأمانة العامة للحكومة sgg.gov.ma)"
)

# Language Selector (Arabic MSA, French, Moroccan Darija)
lang_choice = st.radio(
    "Language / اللغة / الدارجة",
    options=[
        "العربية الفصحى (Arabic MSA)",
        "الدارجة المغربية (Moroccan Darija)",
        "Français (French)",
    ],
    horizontal=True,
)
if "الدارجة" in lang_choice:
    lang_code = "darija"
elif "العربية" in lang_choice:
    lang_code = "ar"
else:
    lang_code = "fr"

# Sidebar Corpus Overview
st.sidebar.header("📚 Moroccan Statutory Corpus")
st.sidebar.markdown(
    """
- **مدونة الأسرة** (*Moudawana* — Loi 70-03)
- **مدونة الشغل** (*Code du Travail* — Loi 65-99)
- **مدونة التجارة والشركات** (*SARL / Chèque* — Loi 5-96 / 19-20)
- **الكراء السكني والمهني** (*Baux d'habitation* — Loi 67-12)
- **مجموعة القانون الجنائي** (*Code Pénal* — Loi 103-13 / 03-23)
- **قانون الالتزامات والعقود** (*DOC* — Dahir 1913)
- **حماية المعطيات الشخصية** (*CNDP* — Loi 09-08)
"""
)
st.sidebar.divider()
st.sidebar.markdown(
    """
### 🛡️ Citation Safety Guarantee
1. **Verbatim Statutory Text** is rendered in an immutable gold-bordered block with exact **Dahir**, **Law #**, **BO Issue #**, and **Publication Date**.
2. **AI Commentary** is strictly separated in a blue explanatory block.
3. **Anti-Hallucination Gate** verifies that every cited article exists in the retrieved statutory corpus.
"""
)

rag = MoroccanLegalRAG()
bo_engine = BulletinOfficielDiffEngine()
contract_auditor = MoroccanContractAuditor()

tab_qa, tab_bo, tab_custom_diff, tab_contract = st.tabs(
    [
        "💬 1. Legal Q&A & Darija Translator",
        "📜 2. Jarida Rasmiya (BO) Redline Alerts",
        "🔬 3. Custom Article Redline Comparator",
        "🛡️ 4. Moroccan Contract Compliance Auditor",
    ]
)

with tab_qa:
    st.subheader("🔍 Ask in Arabic, French, or Moroccan Darija (العربية / الدارجة / Français)")
    preset_queries = {
        "ar": "ما هي حقوق الأجير في حالة الطرد التعسفي وساعات العمل القانونية؟",
        "darija": "جراو عليا من الخدمة بلا سابق إنذار وبغيت نعرف التعويض ديالي",
        "fr": "Quels sont les droits du salarié en cas de licenciement abusif et préavis ?",
    }
    user_query = st.text_input(
        "Enter your question / اطرح سؤالك القانوني أو بالدارجة:",
        value=preset_queries[lang_code],
    )

    col_ex1, col_ex2, col_ex3 = st.columns(3)
    with col_ex1:
        if st.button("🏠 Moudawana / Divorce (الشقاق)"):
            user_query = "بغيت نطلق بالشقاق وشنو هي النفقة والحضانة؟"
    with col_ex2:
        if st.button("🏢 SARL Capital & Check Bounce"):
            user_query = "bghit nssess charika SARL chhal lcapital w chno 3oqobat cheque bla rssid"
    with col_ex3:
        if st.button("🔑 Lease Eviction (الإفراغ والكراء)"):
            user_query = "moul dar bgha ykhrjni mn lkra bla ma y3lemni"

    if st.button("⚖️ Retrieve Grounded Statutory Citations", type="primary"):
        result = rag.answer_query(user_query, lang=lang_code)
        translation = result["query_translation"]

        badge_col1, badge_col2, badge_col3 = st.columns(3)
        with badge_col1:
            if result["citation_verified"]:
                st.markdown(
                    '<span class="verified-badge">✅ Anti-Hallucination Gate: Citations Verified</span>',
                    unsafe_allow_html=True,
                )
        with badge_col2:
            st.info(f"**Detected Legal Domain:** `{result['detected_domain']}`")
        with badge_col3:
            st.info(
                f"**Darija Query Bridge:** `{'Active' if translation['detected_darija'] else 'Standard MSA/FR'}`"
            )

        if translation["detected_darija"] and translation["expanded_terms"]:
            with st.expander("🗣️ Darija → Statutory Terminology Expansion"):
                st.write("Matched colloquial Moroccan phrases expanded into formal legal keywords:")
                st.code(", ".join(translation["expanded_terms"]))

        st.markdown("### 📜 1. Verbatim Statutory Citations (نصوص قانونية حرفية موثقة)")
        for cit in result["verbatim_citations"]:
            st.markdown(
                f"""
                <div class="verbatim-box">
                    <strong>{cit['code']} — {cit['article']}</strong><br/>
                    <small>📜 {cit['dahir']} | 📰 الجريدة الرسمية: <code>{cit['bo_issue']}</code> ({cit['publication_date']}) | قانون رقم: <code>{cit['law_number']}</code></small>
                    <hr style="border-color:#334155;margin:8px 0;"/>
                    <p dir="rtl" style="font-size:1.02rem;margin-bottom:6px;"><strong>النص العربي الحرفي:</strong> {cit['text_ar']}</p>
                    <p style="font-size:0.95rem;color:#cbd5e1;margin-bottom:0;"><strong>Texte Officiel (FR):</strong> {cit['text_fr']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("### 💡 2. AI Simplified Explanation (شرح مبسط منفصل عن النص الرسمي)")
        st.markdown(
            f"""
            <div class="commentary-box">
                <strong>🧠 الشرح بالدارجة المغربية (Moroccan Darija):</strong><br/>
                <p dir="rtl">{result['ai_commentary']['darija']}</p>
                <hr style="border-color:#334155;margin:8px 0;"/>
                <strong>📘 الشرح بالعربية الفصحى (MSA):</strong><br/>
                <p dir="rtl">{result['ai_commentary']['ar']}</p>
                <hr style="border-color:#334155;margin:8px 0;"/>
                <strong>🇫🇷 Synthèse Explicative (Français):</strong><br/>
                <p>{result['ai_commentary']['fr']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.warning(result["legal_disclaimer"])

with tab_bo:
    st.subheader(
        "📰 Official Gazette (Jarida Rasmiya — الجريدة الرسمية) Redline Diff & Compliance Alerts"
    )
    st.markdown(
        "Automated article-by-article diffing of Moroccan legislative reforms published by the Secrétariat Général du Gouvernement (`sgg.gov.ma`)."
    )

    audience_filter = st.selectbox(
        "Filter by Target Compliance Audience / تصفية حسب الفئة المعنية:",
        options=[
            "ALL (الكل)",
            "SMEs",
            "Accountants",
            "Corporate Lawyers",
            "HR",
            "Tech Startups",
            "DPOs",
            "Lawyers",
            "Citizens",
        ],
    )
    selected_audience = None if audience_filter.startswith("ALL") else audience_filter
    issues = bo_engine.list_bo_issues(audience=selected_audience)

    for issue in issues:
        with st.container():
            st.markdown(
                f"### 📌 {issue['bo_number']} — {issue['title_ar']} / *{issue['title_fr']}*"
            )
            st.caption(
                f"📅 Publication Date: `{issue['publication_date']}` | 🔗 Source: [{issue['source_url']}]({issue['source_url']}) | 🎯 Audience: `{', '.join(issue['target_audience'])}`"
            )
            for am in issue["amendments"]:
                diff = am["redline_diff"]
                st.markdown(
                    f"**{am['article_ref']}** — Severity: `{diff['compliance_severity']}` (Change Ratio: `{int(diff['change_ratio'] * 100)}%`)"
                )
                st.markdown(
                    f"<div style='background:#0f172a;padding:14px;border-radius:8px;border:1px solid #334155;line-height:1.7;'>{diff['redline_html']}</div>",
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.info(f"**🇲🇦 بالدارجة:**\n\n{am['summary_darija']}")
                with c2:
                    st.info(f"**📘 بالعربية:**\n\n{am['summary_ar']}")
                with c3:
                    st.info(f"**🇫🇷 En Français:**\n\n{am['summary_fr']}")
            st.divider()

with tab_custom_diff:
    st.subheader("🔬 Compare Any Two Statutory Articles (Redline Diff Generator)")
    col_old, col_new = st.columns(2)
    with col_old:
        old_art_input = st.text_area(
            "Old Statutory Article Text (النص القديم):",
            value="Article 46: Le capital de la société à responsabilité limitée doit être de 100.000 dirhams au moins et déposé en banque.",
            height=130,
        )
    with col_new:
        new_art_input = st.text_area(
            "New Bulletin Officiel Text (النص الجديد في الجريدة الرسمية):",
            value="Article 46: Le capital de la société à responsabilité limitée est librement fixé par les associés dans les statuts sans minimum légal.",
            height=130,
        )
    if st.button("⚡ Compute Redline Diff", key="btn_custom_diff"):
        custom_diff = bo_engine.compute_article_redline_diff(
            old_text=old_art_input,
            new_text=new_art_input,
            article_ref="Custom Article Comparison",
            bo_issue="Custom BO Issue",
        )
        st.markdown(
            f"**Compliance Severity:** `{custom_diff['compliance_severity']}` | **Change Ratio:** `{int(custom_diff['change_ratio'] * 100)}%`"
        )
        st.markdown(
            f"<div style='background:#0f172a;padding:16px;border-radius:8px;border:1px solid #475569;line-height:1.8;'>{custom_diff['redline_html']}</div>",
            unsafe_allow_html=True,
        )

with tab_contract:
    st.subheader("🛡️ Moroccan Contract & Clause Compliance Auditor")
    st.markdown(
        "Paste any Moroccan employment contract (*CDI/CDD*), commercial/residential lease (*Bail*), or data privacy clause to check for statutory nullities."
    )
    sample_contract_text = """CONTRAT DE TRAVAIL À DURÉE INDÉTERMINÉE (CDI)
Article 1 : La période d'essai pour l'employé est fixée à 12 mois renouvelable deux fois.
Article 2 : Le salarié renonce par avance à toute indemnité de licenciement abusif.
Article 3 : Les données biométriques du salarié sont collectées sans déclaration préalable à la CNDP."""

    contract_input = st.text_area(
        "Contract Clauses / بنود العقد للمراجعة القانونية:",
        value=sample_contract_text,
        height=160,
    )
    if st.button("🛡️ Audit Contract Against Moroccan Law", type="primary"):
        audit_lang = "ar" if lang_code in ("ar", "darija") else "fr"
        report = contract_auditor.audit_contract(contract_input, lang=audit_lang)

        score_col1, score_col2 = st.columns(2)
        with score_col1:
            st.metric("Statutory Risk Score (0-100)", f"{report['risk_score']} / 100")
        with score_col2:
            st.metric("Overall Compliance Status", report["status"])

        for v in report["violations"]:
            st.error(
                f"🚨 **{v['severity']} — {v['statutory_reference']}**\n\n"
                f"- **Finding:** {v['Explanation']}\n"
                f"- **Remediation:** {v['Remediation']}"
            )

        st.caption(report["disclaimer"])
