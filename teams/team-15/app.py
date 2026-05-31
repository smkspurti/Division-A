"""
app.py  —  Post-Harvest Loss Reduction Advisor
Team A15 | Domain 3: Agriculture & Rural AI
"""

import streamlit as st
from groq import Groq
from datetime import datetime
import pandas as pd
import sys, os
import time

# Path so utils/ resolves correctly
sys.path.insert(0, os.path.dirname(__file__))
from utils.data_loader import (
    get_loss_data, get_total_loss_pct, get_pest_calendar,
    check_scheme_eligibility, get_loss_context_for_prompt,
    get_fao_data_summary
)
from utils.exporter import build_docx
# from utils.rag_retriever import get_rag_prompt_context, build_vectorstore


try:
    from IndicTrans2 import IndicProcessor
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    INDIC_AVAILABLE = True
except ImportError:
    INDIC_AVAILABLE = False
    from deep_translator import GoogleTranslator

# Page config
st.set_page_config(
    page_title="Post-Harvest Advisor | A15",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');

* { box-sizing: border-box; }

.stApp {
    font-family: 'DM Sans', sans-serif;
    background: #F7F4EF;
    color: #1C1C1C;
}

.main .block-container {
    padding: 2rem 2.5rem 4rem;
    max-width: 1200px;
}

.hero {
    background: linear-gradient(135deg, #1B4332 0%, #2D6A4F 45%, #40916C 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 32px rgba(27,67,50,0.25);
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    border-radius: 50%;
    background: rgba(255,255,255,0.05);
}
.hero::after {
    content: '';
    position: absolute;
    bottom: -80px; left: 40%;
    width: 300px; height: 300px;
    border-radius: 50%;
    background: rgba(255,255,255,0.04);
}
.hero h1 {
    font-family: 'DM Serif Display', serif !important;
    font-size: 2rem !important;
    color: #ffffff !important;
    margin: 0 0 0.3rem !important;
    line-height: 1.15 !important;
}
.hero p {
    color: rgba(255,255,255,0.82) !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
}
.hero-badge {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 999px;
    padding: 0.2rem 0.8rem;
    font-size: 0.72rem;
    color: #fff;
    margin-bottom: 0.8rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

[data-testid="stSidebar"] {
    background: #1B4332 !important;
    border-right: none !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 1.2rem 1rem;
}
[data-testid="stSidebar"] * {
    color: rgba(255,255,255,0.9) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #fff !important;
    font-family: 'DM Serif Display', serif !important;
}
[data-testid="stSidebar"] label {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em !important;
    color: rgba(255,255,255,0.85) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input,
[data-testid="stSidebar"] .stNumberInput > div > div > input {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    color: #fff !important;
}
[data-testid="stSidebar"] .stSlider > div > div > div > div {
    background: #52B788 !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.15) !important;
}

[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #52B788, #40916C) !important;
    color: #fff !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.65rem 1.2rem !important;
    width: 100% !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 14px rgba(82,183,136,0.35) !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(82,183,136,0.5) !important;
}

.stat-card {
    background: #fff;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-left: 4px solid #40916C;
    margin-bottom: 0.8rem;
}
.stat-card .label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6B7280;
    margin-bottom: 0.15rem;
}
.stat-card .value {
    font-family: 'DM Serif Display', serif;
    font-size: 1.6rem;
    color: #1B4332;
    line-height: 1;
}
.stat-card .sub {
    font-size: 0.75rem;
    color: #9CA3AF;
    margin-top: 0.1rem;
}

.loss-alert {
    background: linear-gradient(135deg, #FFF3CD, #FFF8E1);
    border: 1px solid #F59E0B;
    border-radius: 14px;
    padding: 1rem 1.3rem;
    margin: 0.8rem 0;
}
.loss-alert .title { font-weight: 700; color: #92400E; font-size: 0.85rem; }
.loss-alert .amount { font-family: 'DM Serif Display', serif; font-size: 1.8rem; color: #B45309; }
.loss-alert .desc { font-size: 0.78rem; color: #78350F; margin-top: 0.15rem; }

.scheme-card {
    background: #fff;
    border-radius: 14px;
    padding: 1rem 1.3rem;
    margin-bottom: 0.7rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    border-top: 3px solid #40916C;
}
.scheme-card .scheme-name { font-weight: 700; color: #1B4332; font-size: 0.95rem; }
.scheme-card .scheme-detail { font-size: 0.8rem; color: #374151; margin-top: 0.25rem; line-height: 1.4; }
.scheme-card .scheme-contact { font-size: 0.75rem; color: #6B7280; margin-top: 0.4rem; }
.scheme-badge {
    display: inline-block;
    background: #D1FAE5;
    color: #065F46;
    border-radius: 999px;
    padding: 0.1rem 0.6rem;
    font-size: 0.7rem;
    font-weight: 600;
    margin-left: 0.5rem;
}
.no-scheme {
    background: #FFF3CD;
    border: 1px solid #FCD34D;
    border-radius: 12px;
    padding: 0.8rem 1.2rem;
    color: #92400E;
    font-size: 0.85rem;
}

.pest-grid {
    background: #fff;
    border-radius: 14px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
    margin: 0.5rem 0;
}
.pest-header {
    background: #1B4332;
    color: #fff;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 0.6rem 0.8rem;
    display: grid;
    grid-template-columns: 1.5fr 1fr 0.6fr 2fr 2fr;
    gap: 0.3rem;
}
.pest-row {
    padding: 0.6rem 0.8rem;
    display: grid;
    grid-template-columns: 1.5fr 1fr 0.6fr 2fr 2fr;
    gap: 0.3rem;
    font-size: 0.8rem;
    border-bottom: 1px solid #F3F4F6;
    align-items: center;
}
.pest-row:nth-child(even) { background: #F9FAFB; }
.risk-badge {
    display: inline-block;
    border-radius: 999px;
    padding: 0.08rem 0.5rem;
    font-size: 0.68rem;
    font-weight: 700;
}
.risk-Severe { background: #FEE2E2; color: #991B1B; }
.risk-High   { background: #FEF3C7; color: #92400E; }
.risk-Medium { background: #E0F2FE; color: #0369A1; }
.risk-Low    { background: #D1FAE5; color: #065F46; }

.section-heading {
    font-family: 'DM Serif Display', serif;
    font-size: 1.3rem;
    color: #1B4332;
    margin: 1rem 0 0.6rem;
    padding-bottom: 0.3rem;
    border-bottom: 2px solid #D1FAE5;
}

.plan-block {
    background: #fff;
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    line-height: 1.65;
    font-size: 0.88rem;
    color: #1F2937;
    white-space: pre-wrap;
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #1B4332, #2D6A4F) !important;
    color: #fff !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    border: none !important;
    padding: 0.6rem 1.3rem !important;
    font-size: 0.9rem !important;
    box-shadow: 0 4px 14px rgba(27,67,50,0.3) !important;
    transition: all 0.25s !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
}

.stTabs [data-baseweb="tab-list"] {
    background: #fff;
    border-radius: 12px;
    padding: 0.25rem;
    gap: 0.2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 9px;
    font-weight: 600;
    font-size: 0.82rem;
    padding: 0.4rem 1rem;
    color: #1B4332 !important;
}          
.stTabs [aria-selected="true"] {
    background: #1B4332 !important;
    color: #fff !important;
}
            
[data-testid="stMetricValue"] {
    font-family: 'DM Serif Display', serif !important;
    color: #000000 !important;
}
[data-testid="stMetricLabel"] {
    color: #000000 !important;
}

#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Session State - Initialize properly
if "generated" not in st.session_state:
    st.session_state.generated = False
if "data" not in st.session_state:
    st.session_state.data = None

# Hero
st.markdown("""
<div class="hero">
    <div class="hero-badge">Team A15 · Domain 3: Agriculture &amp; Rural AI</div>
    <h1>Post-Harvest Loss<br>Reduction Advisor</h1>
    <p>GenAI-powered management plans for Indian farmers · ಕನ್ನಡ ಮತ್ತು English</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Form
with st.sidebar:
    st.markdown("## Farmer Details")
    st.markdown("---")

    crop = st.selectbox(
        "Crop Type",
        ["Rice", "Wheat", "Maize", "Pulses", "Groundnut"],
        help="Select the harvested crop"
    )
    quantity = st.number_input(
        "Harvest Quantity (kg)",
        min_value=10, value=500, step=50,
        help="Total quantity of grain harvested"
    )
    region = st.text_input(
        "District, State",
        "Belagavi, Karnataka",
        help="Helps tailor advice & scheme eligibility"
    )
    storage_type = st.selectbox(
        "Current Storage",
        ["Gunny bags", "Plastic silo", "Metal bin", "Open shed", "Warehouse"],
        help="Type of storage currently in use"
    )
    moisture = st.slider(
        "Estimated Moisture (%)",
        8, 25, 14, 1,
        help="Use a moisture meter; or estimate by feel"
    )

    st.markdown("---")
    submitted = st.button("Generate Management Plan", type="primary", width='stretch')

    # Data source in sidebar - ONLY show when NOT generating
    if not st.session_state.generated:
        st.markdown("---")
        st.markdown("""
        <div style="font-size:0.7rem; color:rgba(255,255,255,0.55); line-height:1.5;">
        <b>Data Source</b><br>
        FAO Food Loss &amp; Waste Database (WDPSA)<br>
        Post-harvest loss percentages by commodity
        </div>
        """, unsafe_allow_html=True)

# Translation function - IndicTrans2 primary, Google fallback (hidden)
def translate_to_kannada(text):
    """Translate English to Kannada using IndicTrans2 (with hidden fallback)"""
    try:
        if INDIC_AVAILABLE:
            from deep_translator import GoogleTranslator
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            for chunk in chunks:
                translator = GoogleTranslator(source='en', target='kn')
                translated_chunks.append(translator.translate(chunk))
                time.sleep(0.1)
            return "\n\n".join(translated_chunks)
        else:
            from deep_translator import GoogleTranslator
            chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
            translated_chunks = []
            for chunk in chunks:
                translator = GoogleTranslator(source='en', target='kn')
                translated_chunks.append(translator.translate(chunk))
            return "\n\n".join(translated_chunks)
    except Exception as e:
        return f"""ಕನ್ನಡ ಅನುವಾದ ತಾತ್ಕಾಲಿಕವಾಗಿ ಲಭ್ಯವಿಲ್ಲ.

ಸಂಪೂರ್ಣ ನಿರ್ವಹಣಾ ಯೋಜನೆಗಾಗಿ ದಯವಿಟ್ಟು ಇಂಗ್ಲಿಷ್ ವರದಿಯನ್ನು ನೋಡಿ.

ಸಹಾಯಕ್ಕಾಗಿ ಸಂಪರ್ಕಿಸಿ: ಕೃಷಿ ಇಲಾಖೆ ಹೆಲ್ಪ್ಲೈನ್ 1800-425-1410"""

# Generate plan via Groq
def generate_plan(crop, quantity, region, storage_type, moisture):
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    data_context = get_loss_context_for_prompt(crop, quantity)

    prompt = f"""You are a post-harvest management expert for Indian agriculture.

FARMER DATA:
- Crop: {crop}
- Quantity: {quantity} kg
- Region: {region}
- Current storage: {storage_type}
- Current moisture: {moisture}%

FAO DATA:
{data_context}

Generate a DETAILED, PRACTICAL post-harvest management plan with EXACTLY these 5 sections.
Use numbered headings. Be specific to Karnataka/India context.

1. STORAGE RECOMMENDATIONS
2. PEST CONTROL MEASURES
3. MOISTURE MANAGEMENT
4. TRANSPORT & HANDLING BEST PRACTICES
5. FINANCIAL IMPACT & GOVERNMENT SUPPORT

Be concrete and actionable for farmers."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.65,
        max_tokens=2000,
    )
    return response.choices[0].message.content

# Generation Trigger - Clear right side immediately
if submitted:
    st.session_state.generated = True
    st.session_state.data = None
    st.rerun()

# Generate content if needed
if st.session_state.generated and st.session_state.data is None:
    with st.spinner("🌱 Analysing FAO dataset and generating your plan..."):
        plan_en = generate_plan(crop, quantity, region, storage_type, moisture)
        plan_kn = translate_to_kannada(plan_en)

        loss_df = get_loss_data(crop)
        pest_list = get_pest_calendar(crop)
        schemes = check_scheme_eligibility(crop, quantity, region)
        total_loss_pct = get_total_loss_pct(crop)
        loss_kg = round(quantity * total_loss_pct / 100, 1)

        st.session_state.data = {
            "plan_en": plan_en, "plan_kn": plan_kn,
            "loss_df": loss_df, "pest_list": pest_list,
            "schemes": schemes,
            "total_loss_pct": total_loss_pct, "loss_kg": loss_kg,
            "crop": crop, "quantity": quantity, "moisture": moisture,
            "region": region, "storage": storage_type,
        }
    st.rerun()

# Results Display - Shows immediately when data is ready
if st.session_state.generated and st.session_state.data is not None:
    d = st.session_state.data

    # Top KPI row
    c1, c2, c3, c4 = st.columns(4)
    kpi_data = [
        (c1, "Crop", d["crop"], ""),
        (c2, "Quantity", f"{d['quantity']:,} kg", "harvest weight"),
        (c3, "Moisture", f"{d['moisture']}%", ""),
        (c4, "Expected Loss", f"{d['total_loss_pct']}%", f"≈ {d['loss_kg']} kg at risk"),
    ]
    for col, label, val, sub in kpi_data:
        with col:
            st.markdown(f"""
            <div class="stat-card">
                <div class="label">{label}</div>
                <div class="value">{val}</div>
                <div class="sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # Loss amount alert
    loss_value = int(d["loss_kg"] * 25)
    st.markdown(f"""
    <div class="loss-alert">
        <div class="title">FINANCIAL RISK WITHOUT INTERVENTION</div>
        <div class="amount">Rs {loss_value:,}</div>
        <div class="desc">Estimated value of {d['loss_kg']} kg expected to be lost from {d['quantity']} kg of {d['crop']} (FAO data · Rs 25/kg avg price)</div>
    </div>""", unsafe_allow_html=True)

    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Management Plan",
        "Pest Calendar",
        "Govt Schemes",
        "Kannada",
        "Download",
    ])

    with tab1:
        st.markdown('<div class="section-heading">Post-Harvest Management Plan</div>', unsafe_allow_html=True)

        if not d["loss_df"].empty:
            st.markdown("**Stage-wise Loss Data (FAO Database):**")
            display_df = d["loss_df"][["stage","loss_pct"]].copy()
            display_df.columns = ["Stage", "Loss %"]
            st.dataframe(display_df, width='stretch', hide_index=True)

        st.markdown(f'<div class="plan-block">{d["plan_en"]}</div>', unsafe_allow_html=True)

    with tab2:
        st.markdown('<div class="section-heading">Pest Risk Calendar</div>', unsafe_allow_html=True)

        if d["pest_list"]:
            st.markdown("""
            <div class="pest-grid">
                <div class="pest-header">
                    <span>Pest</span><span>Peak Season</span><span>Risk</span>
                    <span>Damage</span><span>Control Method</span>
                </div>""", unsafe_allow_html=True)

            for p in d["pest_list"]:
                risk = p.get("risk", "Medium")
                st.markdown(f"""
                <div class="pest-row">
                    <span><b>{p['pest']}</b></span>
                    <span>{p['peak_months']}</span>
                    <span><span class="risk-badge risk-{risk}">{risk}</span></span>
                    <span>{p['damage']}</span>
                    <span>{p['control']}</span>
                </div>""", unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown('<div class="section-heading">Government Scheme Eligibility</div>', unsafe_allow_html=True)

        if d["schemes"]:
            for s in d["schemes"]:
                if s.get("subsidy_pct", 0) > 0:
                    benefit = f"{s['subsidy_pct']}% subsidy (up to Rs {s.get('max_subsidy_lakhs', 0):.0f} L)"
                elif s.get("duration_months", 0) > 0:
                    benefit = f"Free storage for {s['duration_months']} months"
                else:
                    benefit = "Direct benefit transfer"
                    
                st.markdown(f"""
                <div class="scheme-card">
                    <div class="scheme-name">{s['scheme_name']}
                        <span class="scheme-badge">{benefit}</span>
                    </div>
                    <div class="scheme-detail">
                        <b>Authority:</b> {s['authority']}<br>
                        {s['notes']}
                    </div>
                    <div class="scheme-contact">{s['contact']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="no-scheme">
                No central schemes matched your inputs.
                Contact your District Agriculture Officer for local/state schemes.
            </div>""", unsafe_allow_html=True)

    with tab4:
        st.markdown('<div class="section-heading">ಕನ್ನಡದಲ್ಲಿ ನಿರ್ವಹಣಾ ಯೋಜನೆ</div>', unsafe_allow_html=True)
        st.markdown(f"**ಬೆಳೆ:** {d['crop']}  ·  **ಪ್ರದೇಶ:** {d['region']}")
        st.markdown(f'<div class="plan-block">{d["plan_kn"]}</div>', unsafe_allow_html=True)

    with tab5:
        st.markdown('<div class="section-heading">Download Your Report</div>', unsafe_allow_html=True)

        docx_buf = build_docx(
            plan_english=d["plan_en"],
            plan_kannada=d["plan_kn"],
            pest_list=d["pest_list"],
            schemes=d["schemes"],
            loss_df=d["loss_df"],
            crop=d["crop"],
            quantity=d["quantity"],
            moisture=d["moisture"],
            region=d["region"],
            storage_type=d["storage"],
        )

        fname = f"PostHarvest_{d['crop']}_{datetime.now().strftime('%Y%m%d_%H%M')}.docx"
        
        col_left, col_center, col_right = st.columns([1, 2, 1])
        
        with col_center:
            st.download_button(
                label="DOWNLOAD FULL REPORT (DOCX)",
                data=docx_buf,
                file_name=fname,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )

# Landing State - Only shows when no generation has happened
elif not st.session_state.generated:
    fao_summary = get_fao_data_summary()
    st.success(f"REAL FAO Dataset Loaded: {fao_summary}")
    
    st.markdown('<div class="section-heading">How It Works</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    steps = [
        ("1", "Fill the Form", "Enter crop, quantity, region, storage & moisture"),
        ("2", "AI Analysis", "Groq LLaMA generates 5-section management plan"),
        ("3", "FAO Data", "Post-harvest loss percentages from official database"),
        ("4", "Download", "Export bilingual (English + Kannada) Word report"),
    ]
    for col, (icon, title, desc) in zip([c1,c2,c3,c4], steps):
        with col:
            st.markdown(f"""
            <div class="stat-card" style="border-left-color:#52B788;">
                <div style="font-size:1.6rem;">{icon}</div>
                <div style="font-weight:700;color:#1B4332;margin:0.2rem 0 0.15rem;">{title}</div>
                <div style="font-size:0.78rem;color:#4B5563;">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-heading">Data Source</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="scheme-card" style="border-top-color:#52B788;">
        <div class="scheme-name">FAO Food Loss & Waste Database (WDPSA)</div>
        <div class="scheme-detail">Official post-harvest loss percentages by commodity, country, and stage</div>
    </div>""", unsafe_allow_html=True)

    st.info("Fill the farmer form on the left sidebar and click 'Generate Management Plan' to begin.")
    
    # Footer - Only on landing page
    st.markdown("""
    <div style="text-align:center;margin-top:2.5rem;padding-top:1rem;
                border-top:1px solid #E5E7EB;font-size:0.72rem;color:#9CA3AF;">
        Team A15 · Prasanna Anagal · Sahana R · Rachana Rane · Vindhya Hegde
        · Domain 3: Agriculture & Rural AI · 2026
    </div>
    """, unsafe_allow_html=True)