import os
import streamlit as st
import utils
import ui_components
import essay_analyzer

# 1. Page Configuration
st.set_page_config(
    page_title="Plagiarism-Aware Student Essay Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Premium Glassmorphism Theme CSS
st.markdown(ui_components.GLASS_CSS, unsafe_allow_html=True)

# 3. Initialize Session State Variables
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "original_text" not in st.session_state:
    st.session_state.original_text = ""
if "asap_metadata" not in st.session_state:
    st.session_state.asap_metadata = None
if "wiki_title" not in st.session_state:
    st.session_state.wiki_title = ""
if "wiki_url" not in st.session_state:
    st.session_state.wiki_url = ""

# Safe migration check for new schema attributes to prevent crash on hot-reloading
if st.session_state.analysis_results and not hasattr(st.session_state.analysis_results, "wikipedia_report"):
    st.session_state.analysis_results = None

# 4. Sidebar Content (Project Metadata & Settings)
with st.sidebar:
    st.markdown('<div style="text-align: center; margin-bottom: 20px;">', unsafe_allow_html=True)
    st.markdown('<h1 style="color: #c084fc; font-size: 1.8rem; font-weight: 700; margin-bottom: 5px;">🎓 Essay Coach</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #94a3b8; font-size: 0.9rem;">GenAI Plagiarism-Aware Writing Tutor</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Load API Key from api_key.txt or OS env
    def load_api_key() -> str:
        key_file = "api_key.txt"
        if os.path.exists(key_file):
            try:
                with open(key_file, "r") as f:
                    content = f.read().strip()
                    # Filter out helper comment lines
                    lines = [line.strip() for line in content.split("\n") if line.strip() and not line.startswith("#")]
                    if lines:
                        return lines[0]
            except Exception:
                pass
        return os.environ.get("GROQ_API_KEY", "")

    api_key = load_api_key()

    # API Connection Status Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #f1f5f9; font-size: 1.1rem; margin-bottom: 12px; font-weight: 600;">⚙️ Connection Status</h3>', unsafe_allow_html=True)
    
    if api_key:
        st.markdown(
            '<div style="background-color: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.35); '
            'padding: 10px; border-radius: 8px; color: #10b981; font-weight: 600; font-size: 0.85rem; text-align: center;">'
            '🟢 Groq Key Active'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background-color: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); '
            'padding: 12px; border-radius: 8px; color: #fca5a5; font-size: 0.85rem; line-height: 1.4;">'
            '🔑 <b>Key Required:</b> Paste your Groq API key inside <b>api_key.txt</b> in the project folder to activate.'
            '</div>',
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # Team Information Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #f1f5f9; font-size: 1.1rem; margin-bottom: 10px; font-weight: 600;">👥 Team A2</h3>', unsafe_allow_html=True)
    st.markdown(
        '<ul style="list-style-type: none; padding-left: 0; color: #cbd5e1; font-size: 0.9rem; line-height: 1.6;">'
        '  <li>✨ <b>Amogh Annigeri</b> (Roll 146)</li>'
        '  <li>✨ <b>Yashaswini M</b> (Roll 163)</li>'
        '  <li>✨ <b>Raveesh N</b> (Roll 160)</li>'
        '</ul>',
        unsafe_allow_html=True
    )
    st.markdown('<div style="font-size: 0.8rem; color: #64748b; margin-top: 10px;">Domain: Education & Learning</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Suggested Datasets Card
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #f1f5f9; font-size: 1.1rem; margin-bottom: 8px; font-weight: 600;">📊 Training corpora</h3>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.4;">'
        '  <b>• PAN Plagiarism 2011:</b> 27K document pairs<br>'
        '  <b>• ASAP Essay Scoring:</b> 13K graded student essays<br>'
        '  <b>• Persuade Corpus 2.0:</b> 26K annotated argumentative essays'
        '</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# 5. Main Content Header
st.markdown('<h1 class="app-title">Plagiarism-Aware Student Essay Coach</h1>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Elevate your academic writing skills with structured feedback, visual comparison, and dynamic paraphrasing suggestions.</p>', unsafe_allow_html=True)

# 6. Tab Selection Routing
tab_upload, tab_dashboard, tab_highlights, tab_polish = st.tabs([
    "📤 Upload & Inputs",
    "📊 Feedback Dashboard",
    "🔍 Originality Coach",
    "✨ Polished draft & Diff"
])

# ==================== TAB 1: UPLOAD & INPUTS ====================
with tab_upload:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<h2 class="section-title">Submit Student Essay</h2>', unsafe_allow_html=True)

    # File uploader or ASAP sample loader
    col_upload, col_sample = st.columns([2, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload Essay Document (supports PDF or Text)",
            type=["pdf", "txt"],
            help="Upload your draft to begin AI coaching."
        )
        
    with col_sample:
        st.markdown('<div style="margin-top: 28px;"></div>', unsafe_allow_html=True)
        if st.button("🎲 Load ASAP Dataset Essay", use_container_width=True, help="Loads a random student essay from training_set_rel3.tsv"):
            sample = utils.get_random_asap_essay()
            if sample:
                st.session_state.original_text = sample["essay_text"]
                st.session_state.asap_metadata = sample
                st.session_state.analysis_results = None  # Clear previous results
                st.rerun()
            else:
                st.error("ASAP dataset file (training_set_rel3.tsv) not found in the d:\\HACKATHON\\DATASET folder!")

    # Handle text extraction
    extracted_text = ""
    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.read()
            if uploaded_file.name.endswith(".pdf"):
                extracted_text = utils.extract_text_from_pdf(file_bytes)
                st.success("Successfully extracted text from PDF!")
            else:
                extracted_text = file_bytes.decode("utf-8")
                st.success("Successfully loaded plain text essay!")
            # Reset metadata if a new file is uploaded
            st.session_state.asap_metadata = None
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

    st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)

    # Display ASAP sample metadata if active
    if st.session_state.asap_metadata:
        meta = st.session_state.asap_metadata
        st.markdown(
            f'<div style="background-color: rgba(139, 92, 246, 0.12); border: 1px solid rgba(139, 92, 246, 0.3); '
            f'padding: 14px; border-radius: 12px; margin-bottom: 18px; color: #cbd5e1; font-size: 0.95rem;">'
            f'  🎯 <b>ASAP Sample Loaded:</b> Essay ID #{meta["essay_id"]} | Prompt Set {meta["essay_set"]} | '
            f'  Original Human Score: <b style="color: #c084fc; font-size: 1.1rem;">{meta["human_score"]}/{meta["max_score"]}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Textarea input fallback
    essay_input = st.text_area(
        "Alternatively, paste your essay text here:",
        value=extracted_text if extracted_text else st.session_state.original_text,
        height=300,
        placeholder="Type or paste your academic essay draft..."
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Trigger Button Container
    st.markdown('<div style="text-align: center; margin-top: 25px; margin-bottom: 25px;">', unsafe_allow_html=True)
    if st.button("🚀 Analyze Essay & Start Coaching", use_container_width=True):
        if not api_key:
            st.warning("⚠️ Groq API key is missing. Please place your key inside 'api_key.txt' in the project directory.")
        elif not essay_input.strip():
            st.warning("⚠️ Please upload a file or paste your essay content before starting.")
        else:
            with st.spinner("Analyzing essay structure with llama-3.3-70b-versatile via Groq Cloud..."):
                try:
                    # Run Backend Groq API Calling
                    analysis, w_title, w_url = essay_analyzer.analyze_essay(essay_input, api_key)
                    st.session_state.analysis_results = analysis
                    st.session_state.wiki_title = w_title
                    st.session_state.wiki_url = w_url
                    st.session_state.original_text = essay_input
                    st.success("🎉 Essay analysis completed successfully! Explore the tabs above to view details.")
                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# ==================== TAB 2: FEEDBACK DASHBOARD ====================
with tab_dashboard:
    if st.session_state.analysis_results is None:
        st.markdown(
            '<div class="glass-card" style="text-align: center; padding: 50px;">'
            '  <h3 style="color: #94a3b8; font-weight: 400;">No essay has been analyzed yet.</h3>'
            '  <p style="color: #64748b; font-size: 0.95rem; margin-top: 10px;">Please upload your essay and click "Analyze Essay" on the first tab to view detailed metrics.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.analysis_results
        
        st.markdown('<h2 class="section-title">Writing Performance Rubric</h2>', unsafe_allow_html=True)
        
        # Display 4 scoring metrics in a responsive card grid
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        
        with m_col1:
            st.markdown(ui_components.render_score_card(
                "💬 Clarity", 
                results.clarity.score, 
                "Measures readability, flow, sentence logic, and structure."
            ), unsafe_allow_html=True)
            
        with m_col2:
            st.markdown(ui_components.render_score_card(
                "⚖️ Argument", 
                results.argument.score, 
                "Assesses the strength of your thesis statement and structure."
            ), unsafe_allow_html=True)
            
        with m_col3:
            st.markdown(ui_components.render_score_card(
                "📚 Evidence", 
                results.evidence.score, 
                "Checks research support, facts, citation, and sound arguments."
            ), unsafe_allow_html=True)
            
        with m_col4:
            st.markdown(ui_components.render_score_card(
                "✍️ Grammar", 
                results.grammar.score, 
                "Evaluates spelling, punctuation, passive voice, and phrasing."
            ), unsafe_allow_html=True)

        st.markdown('<h2 class="section-title">Detailed Feedback & Coaching Insights</h2>', unsafe_allow_html=True)

        # Detailed expandable reports for each dimension
        col_feedback1, col_feedback2 = st.columns(2)
        
        with col_feedback1:
            # Clarity Expandable Card
            with st.expander("💬 Expand Clarity Insights", expanded=True):
                st.markdown("#### **Strengths**")
                for s in results.clarity.strengths:
                    st.markdown(f"- ✅ {s}")
                st.markdown("#### **Required Improvements**")
                for i in results.clarity.improvements:
                    st.markdown(f"- 💡 {i}")

            # Evidence Expandable Card
            with st.expander("📚 Expand Evidence Insights", expanded=True):
                st.markdown("#### **Strengths**")
                for s in results.evidence.strengths:
                    st.markdown(f"- ✅ {s}")
                st.markdown("#### **Required Improvements**")
                for i in results.evidence.improvements:
                    st.markdown(f"- 💡 {i}")

        with col_feedback2:
            # Argument Expandable Card
            with st.expander("⚖️ Expand Argument Insights", expanded=True):
                st.markdown("#### **Strengths**")
                for s in results.argument.strengths:
                    st.markdown(f"- ✅ {s}")
                st.markdown("#### **Required Improvements**")
                for i in results.argument.improvements:
                    st.markdown(f"- 💡 {i}")

            # Grammar Expandable Card
            with st.expander("✍️ Expand Grammar Insights", expanded=True):
                st.markdown("#### **Strengths**")
                for s in results.grammar.strengths:
                    st.markdown(f"- ✅ {s}")
                st.markdown("#### **Required Improvements**")
                for i in results.grammar.improvements:
                    st.markdown(f"- 💡 {i}")

# ==================== TAB 3: ORIGINALITY COACH ====================
with tab_highlights:
    if st.session_state.analysis_results is None:
        st.markdown(
            '<div class="glass-card" style="text-align: center; padding: 50px;">'
            '  <h3 style="color: #94a3b8; font-weight: 400;">No essay has been analyzed yet.</h3>'
            '  <p style="color: #64748b; font-size: 0.95rem; margin-top: 10px;">Please upload your essay and click "Analyze Essay" on the first tab to highlight unoriginal text.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.analysis_results
        
        st.markdown('<h2 class="section-title">Interactive Originality Highlighter</h2>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 20px;">'
            '🕵️ The coach has scanned your essay. Phrases highlighted in <b style="color: #f59e0b;">amber</b> show unoriginal, '
            'robotic, or repetitive phrasing. <b>Hover over any highlighted phrase</b> to see specific editing suggestions!'
            '</p>',
            unsafe_allow_html=True
        )

        # Dynamic Highlighter HTML Renderer
        highlighted_html = ui_components.build_highlighted_essay_html(
            st.session_state.original_text, 
            results.flagged_phrases
        )
        st.markdown(highlighted_html, unsafe_allow_html=True)
        
        # Display flagged phrases as a readable list inside expander
        st.markdown('<div style="margin-top: 25px;"></div>', unsafe_allow_html=True)
        with st.expander("📝 Show Flagged Phrase Summary List"):
            if not results.flagged_phrases:
                st.info("No unoriginal or plagiarized phrases flagged! Exceptional original writing!")
            else:
                for idx, fp in enumerate(results.flagged_phrases):
                    st.markdown(f"**Phrase {idx+1}:** `\"{fp.phrase}\"`")
                    st.markdown(f"- **Coach Assessment:** *{fp.reason}*")
                    st.markdown("- **Rephrasing Alternatives:**")
                    for sug in fp.suggestions:
                        st.markdown(f"  - 🟢 *\"{sug}\"*")
                    st.markdown("---")

        # Wikipedia Semantic Plagiarism Scan
        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-title">🌐 Wikipedia Semantic Plagiarism Audit</h2>', unsafe_allow_html=True)
        
        wiki_rep = results.wikipedia_report
        wiki_val = wiki_rep.similarity_score
        
        # Threat Color Styling (Green: safe, Amber: warning, Red: danger)
        wiki_cls = "score-high" if wiki_val < 30 else ("score-medium" if wiki_val <= 65 else "score-low")
        
        st.markdown(
            f'<div class="glass-card" style="margin-top: 15px;">'
            f'  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">'
            f'      <div style="font-size: 1.25rem; font-weight: 600; color: #f1f5f9;">'
            f'          📖 Cross-Reference Match: <a href="{st.session_state.wiki_url}" target="_blank" style="color: #c084fc; text-decoration: underline;">{st.session_state.wiki_title}</a>'
            f'      </div>'
            f'      <div class="score-badge {wiki_cls}" style="font-size: 1.4rem; padding: 6px 20px; border-radius: 12px;">'
            f'          {wiki_val}% Similarity'
            f'      </div>'
            f'  </div>'
            f'  <div style="font-size: 1rem; font-weight: 650; color: #f1f5f9; margin-bottom: 8px;">Verdict: {wiki_rep.verdict}</div>'
            f'  <div style="font-size: 0.95rem; color: #cbd5e1; line-height: 1.6; text-align: left; padding: 15px; border-radius: 10px; background: rgba(0,0,0,0.25); border: 1px solid rgba(255,255,255,0.03);">'
            f'      💡 <b>Semantic Assessment:</b> {wiki_rep.summary}'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )
        
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
        with st.expander("🕵️ Show Sentence-Level Wikipedia Overlaps", expanded=True):
            if not wiki_rep.matches:
                st.success("No sentence-level matches found! Excellent original writing relative to the Wikipedia reference text.")
            else:
                for idx, m in enumerate(wiki_rep.matches):
                    type_color = "#38bdf8" if m.similarity_type == "Paraphrased Match" else "#ef4444"
                    st.markdown(
                        f'<div style="background: rgba(255,255,255,0.015); border: 1px solid rgba(255,255,255,0.03); '
                        f'padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 4px solid {type_color};">'
                        f'  <span style="background-color: {type_color}; color: #000000; padding: 2px 8px; '
                        f'  border-radius: 4px; font-size: 0.75rem; font-weight: 700; margin-bottom: 10px; display: inline-block;">'
                        f'    {m.similarity_type.upper()}'
                        f'  </span>'
                        f'  <div style="font-size: 0.95rem; color: #cbd5e1; margin-bottom: 8px;"><b>Student Draft Sentence:</b> <span style="font-style: italic;">"{m.student_phrase}"</span></div>'
                        f'  <div style="font-size: 0.95rem; color: #94a3b8;"><b>Wikipedia Source Passage:</b> <span style="font-style: italic;">"{m.wikipedia_fact}"</span></div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

# ==================== TAB 4: POLISHED DRAFT & DIFF ====================
with tab_polish:
    if st.session_state.analysis_results is None:
        st.markdown(
            '<div class="glass-card" style="text-align: center; padding: 50px;">'
            '  <h3 style="color: #94a3b8; font-weight: 400;">No essay has been analyzed yet.</h3>'
            '  <p style="color: #64748b; font-size: 0.95rem; margin-top: 10px;">Please upload your essay and click "Analyze Essay" on the first tab to review the improved draft.</p>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        results = st.session_state.analysis_results

        st.markdown('<h2 class="section-title">Coached Essay Diff</h2>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 20px;">'
            'Visualizes the word-level differences between your original draft and the revised draft. '
            'Deleted text is highlighted in <span class="diff-del" style="font-size: 0.85rem;">red strikethrough</span> and improvements in '
            '<span class="diff-ins" style="font-size: 0.85rem;">green</span>.'
            '</p>',
            unsafe_allow_html=True
        )

        # Diff View Generator
        diff_html = utils.generate_diff_html(st.session_state.original_text, results.improved_draft)
        st.markdown(f'<div class="diff-viewer">{diff_html}</div>', unsafe_allow_html=True)

        st.markdown('<h2 class="section-title">Polished & Revised Essay Draft</h2>', unsafe_allow_html=True)
        st.markdown(
            '<p style="color: #94a3b8; font-size: 0.95rem; margin-bottom: 15px;">'
            'Here is the complete, high-quality, edited version of your essay drafted by the coach.'
            '</p>',
            unsafe_allow_html=True
        )
        
        # Display the draft inside clean viewer box
        st.markdown(f'<div class="essay-viewer">{results.improved_draft}</div>', unsafe_allow_html=True)

        # Download / Copy Action Buttons
        st.markdown('<div style="margin-top: 20px;"></div>', unsafe_allow_html=True)
        st.download_button(
            label="💾 Download Coached Essay Draft (.txt)",
            data=results.improved_draft,
            file_name="polished_essay_draft.txt",
            mime="text/plain",
            use_container_width=True
        )
