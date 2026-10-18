"""
Moroccan Law AI Assistant - Interactive Streamlit Web Interface
Bilingual Arabic & French Legal Consultation & Document Retrieval
"""

import streamlit as st
from src.arabic_nlp import MoroccanLegalNLP
from src.legal_rag import MoroccanLegalRAG

st.set_page_config(
    page_title="Moroccan Law AI | المساعد القانوني المغربي الذكي",
    page_icon="⚖️",
    layout="wide",
)

st.title("⚖️ Moroccan Law AI Assistant | المساعد القانوني المغربي")
st.markdown("Consult Moroccan Legal Codes (Moudawana, Code du Travail, Code Pénal, DOC) with AI-powered RAG.")

# Language selection
lang = st.radio("Language / اللغة", options=["العربية (Arabic)", "Français (French)"], horizontal=True)
lang_code = "ar" if "العربية" in lang else "fr"

# Sidebar Quick Topics
st.sidebar.header("📚 Legal Codes / النصوص القانونية")
st.sidebar.markdown("""
- **مدونة الأسرة** (Code de la Famille - Moudawana)
- **مدونة الشغل** (Code du Travail)
- **مجموعة القانون الجنائي** (Code Pénal)
- **قانون الالتزامات والعقود** (Dahir des Obligations et Contrats - DOC)
- **مدونة التجارة** (Code de Commerce)
""")

rag = MoroccanLegalRAG()

# Query input
default_prompt = "ما هي حقوق الأجير في حالة الطرد التعسفي؟" if lang_code == "ar" else "Quels sont les droits du salarié en cas de licenciement abusif ?"
user_query = st.text_input("Enter your legal inquiry / اطرح استفسارك القانوني:", value=default_prompt)

if st.button("🔍 Search & Analyze / تحليل واستشارة", type="primary"):
    with st.spinner("Analyzing legal articles... / جاري البحث في النصوص القانونية..."):
        result = rag.answer_query(user_query, lang=lang_code)

        st.subheader("📋 Legal Analysis & Citations / الاستشارة والاستشهادات القانونية")
        st.markdown(result["response"])

        with st.expander("🔍 Matched Articles Details / تفاصيل الفصول القانونية"):
            for art in result["matched_articles"]:
                st.write(f"**{art['code']} - {art['article']}**")
                st.write(f"**Arabic**: {art['text_ar']}")
                st.write(f"**French**: {art['text_fr']}")
                st.divider()

st.sidebar.info("💡 Powered by Fast Local NLP & Moroccan Legal RAG Engine.")
