import streamlit as st
import os, tempfile, time

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Ensure API key is configured
if "GOOGLE_API_KEY" not in os.environ:
    st.warning("⚠️ GOOGLE_API_KEY not found in environment. Please add it to your .env file.")



st.set_page_config(page_title="Nyaya-Sahayak: AI FIR Translator", page_icon="⚖️", layout="wide")

from src.parser import parse_fir_pdf
from src.agents import FIRProcessingAgents
from src.rag_engine import LegalRAGEngine
from src.translator import FIRTranslator

@st.cache_resource
def load_models():
    rag = LegalRAGEngine()
    rag.initialize_vector_store()
    return rag, FIRProcessingAgents(llm_provider="gemini"), FIRTranslator(fallback_llm_provider="gemini")

def main():
    st.title("⚖️ Nyaya-Sahayak: Intelligent FIR Translator & Simplifier")
    st.markdown("Transform complex legal documents into plain, accessible language with advanced BNS verification.")
    
    rag_engine, agents, translator = load_models()
    
    st.sidebar.header("📁 Document Upload")
    uploaded_file = st.sidebar.file_uploader("Upload FIR (PDF/Image/Text)", type=["pdf", "jpg", "jpeg", "png", "txt"])
    st.sidebar.header("🗣️ Complainant Statement")
    statement = st.sidebar.text_area("Optional: Enter what the complainant originally reported to the police...", height=150)
    st.sidebar.header("🌐 Language Output")
    target_lang = st.sidebar.radio("Translate to:", ["English Only", "Hindi", "Kannada"])
    process_btn = st.sidebar.button("Analyze FIR")

    if process_btn and uploaded_file:
        with st.spinner("Analyzing Document..."):
            file_extension = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            md_text = parse_fir_pdf(tmp_path)
            os.unlink(tmp_path)
            st.success("Document parsed successfully!")
            
            st.subheader("1. Extracted FIR Details")
            with st.spinner("Gemini extracting structured data..."):
                details = agents.extract_fir_details(md_text)
                col1, col2, col3 = st.columns(3)
                col1.metric("Date Filed", details.get("date_filed", "N/A"))
                col2.metric("Police Station", details.get("police_station", "N/A"))
                col3.metric("Accused Name", details.get("accused_name", "N/A"))
                st.write("**Sections Invoked:**")
                st.write(", ".join(details.get("sections_invoked", [])))
            
            st.subheader("2. Legal Explanations (BNS/IPC)")
            with st.spinner("Querying Legal Vector Database..."):
                for sec in details.get("sections_invoked", []):
                    st.info(f"**{sec}**: {rag_engine.get_section_details(sec)}")
                narrative = details.get("legal_narrative", "")
                if narrative:
                    st.write("---")
                    st.write("**AI Recommended Sections (Based on Narrative Analysis):**")
                    for r in rag_engine.recommend_sections(narrative, k=2):
                        st.success(f"- **{r['section']}** ({r['title']})")
            
            st.subheader("3. Plain-Language Narrative")
            with st.spinner("Simplifying legal jargon..."):
                final_text = agents.simplify_narrative(narrative)
                if target_lang == "Hindi":
                    with st.spinner("Translating..."): final_text = translator.translate_to_hindi(final_text)
                elif target_lang == "Kannada":
                    with st.spinner("Translating..."): final_text = translator.translate_to_kannada(final_text)
                st.markdown(f"**Translation:**\n{final_text}")
            
            if statement:
                st.subheader("4. Discrepancy Analysis")
                with st.spinner("Checking for discrepancies..."): st.warning(agents.check_discrepancies(statement, narrative))
            

if __name__ == "__main__":
    main()
