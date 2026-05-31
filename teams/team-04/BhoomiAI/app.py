# app.py
# Main Streamlit application — AI Land Mutation Generator

import streamlit as st
import pandas as pd
import json
import os
from modules.ui_styles import get_custom_css
from modules.validator import validate_form
from modules.checklist import generate_checklist, get_processing_info
from modules.generator import generate_application, get_sample_record
from modules.translator import translate_to_kannada
from modules.doc_generator import generate_docx
from modules.pdf_generator import generate_pdf
from modules.language_manager import t, init_language, toggle_language, set_language, get_language

init_language()

# ── Page Config ──
st.set_page_config(
    page_title=f"{t('app_title')} — {t('app_subtitle')}",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Inject CSS ──
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ── Load Data ──
@st.cache_data
def load_land_records():
    try:
        df = pd.read_csv("data/karnataka_land_records_29495.csv")
        return df
    except:
        return pd.DataFrame()

@st.cache_data
def load_districts():
    try:
        with open("data/districts.json") as f:
            return json.load(f)
    except:
        return {"districts": [], "taluks": {}, "villages": {}}

@st.cache_data
def load_faq():
    try:
        return pd.read_csv("data/faq_dataset.csv")
    except:
        return pd.DataFrame()

df = load_land_records()
districts_data = load_districts()
faq_df = load_faq()

# ── Sidebar ──
with st.sidebar:
    st.markdown(f"""
    <div style='text-align:center; padding: 20px 0;'>
        <div style='font-size:2.5em;'>🏛️</div>
        <div style='font-size:1.3em; font-weight:700; color:#85c1e9;'>{t('app_title')}</div>
        <div style='font-size:0.75em; color:#888; margin-top:4px;'>{t('app_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### {t('nav_title')}")
    
    # Modern language toggle (pill-like)
    curr_lang = st.session_state.get("lang", "en")
    lang_en = t("lang_en")
    lang_kn = t("lang_kn")
    col_l1, col_l2 = st.columns([1, 1])
    with col_l1:
        if st.button(lang_en, key="lang_en_btn", use_container_width=True):
            set_language("en")
    with col_l2:
        if st.button(lang_kn, key="lang_kn_btn", use_container_width=True):
            set_language("kn")

    st.markdown(f"""<div style='text-align:center; margin-top:8px;'><span class='lang-indicator'>{lang_en if curr_lang=='en' else lang_kn}</span></div>""", unsafe_allow_html=True)

    page_labels = {
        t("nav_home"): "home",
        t("nav_apply"): "apply",
        t("nav_dataset"): "dataset",
        t("nav_faq"): "faq"
    }

    page = st.radio(
        "",
        list(page_labels.keys()),
        label_visibility="collapsed"
    )

    st.markdown("---")

    if not df.empty:
        st.markdown(f"### {t('sidebar_stats')}")
        _total = f"{len(df):,}"
        _districts = df['district'].nunique()
        _mutations = df['mutation_type'].nunique()
        st.markdown(f"""
        <div class='metric-card' style='margin-bottom:10px;'>
            <div class='metric-value'>{_total}</div>
            <div class='metric-label'>{t('stat_records')}</div>
        </div>
        <div class='metric-card' style='margin-bottom:10px;'>
            <div class='metric-value'>{_districts}</div>
            <div class='metric-label'>{t('stat_districts')}</div>
        </div>
        <div class='metric-card'>
            <div class='metric-value'>{_mutations}</div>
            <div class='metric-label'>{t('stat_mutations')}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div style='font-size:0.75em; color:#666; text-align:center;'>
        {t('powered_by')}<br/>
        © 2025 {t('app_title')}
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════
# PAGE: HOME
# ════════════════════════════════════════
if page_labels[page] == "home":

    st.markdown(f"""
    <div class='hero-banner'>
        <div class='hero-title'>{t('home_hero_title')}</div>
        <div class='hero-subtitle'>{t('home_hero_subtitle')}</div>
        <div class='hero-badge'>{t('home_hero_badge')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>29K+</div>
            <div class='metric-label'>{t('stat_records')}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>31</div>
            <div class='metric-label'>{t('stat_districts')}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>3</div>
            <div class='metric-label'>{t('stat_mutations')}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-value'>2</div>
            <div class='metric-label'>{t('lang_toggle')}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<div class='section-header'>{t('home_key_features')}</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_1_title')}</h3>
            <p style='color:#aaa;'>{t('feature_1_desc')}</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_2_title')}</h3>
            <p style='color:#aaa;'>{t('feature_2_desc')}</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_3_title')}</h3>
            <p style='color:#aaa;'>{t('feature_3_desc')}</p>
        </div>""", unsafe_allow_html=True)

    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_4_title')}</h3>
            <p style='color:#aaa;'>{t('feature_4_desc')}</p>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_5_title')}</h3>
            <p style='color:#aaa;'>{t('feature_5_desc')}</p>
        </div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""<div class='glass-card'>
            <h3>{t('feature_6_title')}</h3>
            <p style='color:#aaa;'>{t('feature_6_desc')}</p>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"<div class='section-header'>{t('home_how_it_works')}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='glass-card'>
        <div style='display:flex; justify-content:space-around; flex-wrap:wrap; text-align:center;'>
            <div style='padding:15px;'>
                <div style='font-size:2em;'>📝</div>
                <div style='color:#85c1e9; font-weight:600;'>{t('step_1')}</div>
                <div style='color:#888; font-size:0.85em;'>{t('step_1_desc')}</div>
            </div>
            <div style='padding:15px; font-size:1.5em; color:#3498db; align-self:center;'>→</div>
            <div style='padding:15px;'>
                <div style='font-size:2em;'>✅</div>
                <div style='color:#85c1e9; font-weight:600;'>{t('step_2')}</div>
                <div style='color:#888; font-size:0.85em;'>{t('step_2_desc')}</div>
            </div>
            <div style='padding:15px; font-size:1.5em; color:#3498db; align-self:center;'>→</div>
            <div style='padding:15px;'>
                <div style='font-size:2em;'>🤖</div>
                <div style='color:#85c1e9; font-weight:600;'>{t('step_3')}</div>
                <div style='color:#888; font-size:0.85em;'>{t('step_3_desc')}</div>
            </div>
            <div style='padding:15px; font-size:1.5em; color:#3498db; align-self:center;'>→</div>
            <div style='padding:15px;'>
                <div style='font-size:2em;'>🌐</div>
                <div style='color:#85c1e9; font-weight:600;'>{t('step_4')}</div>
                <div style='color:#888; font-size:0.85em;'>{t('step_4_desc')}</div>
            </div>
            <div style='padding:15px; font-size:1.5em; color:#3498db; align-self:center;'>→</div>
            <div style='padding:15px;'>
                <div style='font-size:2em;'>⬇️</div>
                <div style='color:#85c1e9; font-weight:600;'>{t('step_5')}</div>
                <div style='color:#888; font-size:0.85em;'>{t('step_5_desc')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════
# PAGE: APPLY NOW
# ════════════════════════════════════════
elif page_labels[page] == "apply":

    st.markdown(f"""
    <div class='hero-banner' style='padding:25px;'>
        <div style='font-size:1.8em; font-weight:700; color:white;'>{t('form_hero_title')}</div>
        <div style='color:#85c1e9; margin-top:5px;'>{t('form_hero_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    col_demo, col_space = st.columns([1, 3])
    with col_demo:
        if st.button(t("btn_demo")):
            sample = get_sample_record()
            for key, val in sample.items():
                st.session_state[f"field_{key}"] = val
            st.success(t("demo_success"))

    st.markdown(f"<div class='section-header'>{t('sec_applicant')}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        applicant_name = st.text_input(
            t("lbl_fullname"),
            value=st.session_state.get("field_applicant_name", ""),
            placeholder=t("ph_fullname")
        )
        aadhaar = st.text_input(
            t("lbl_aadhaar"),
            value=st.session_state.get("field_aadhaar", ""),
            placeholder=t("ph_aadhaar"),
            max_chars=12
        )
    with col2:
        mobile = st.text_input(
            t("lbl_mobile"),
            value=st.session_state.get("field_mobile", ""),
            placeholder=t("ph_mobile"),
            max_chars=10
        )
        mutation_type = st.selectbox(
            t("lbl_mutation_type"),
            [t("val_sale"), t("val_inheritance"), t("val_gift")],
            index=0
        )

    st.markdown(f"<div class='section-header'>{t('sec_location')}</div>", unsafe_allow_html=True)

    # Prefer the authoritative districts/taluks/villages from districts.json
    if districts_data and districts_data.get("districts"):
        district_list = sorted(districts_data.get("districts"))
    elif not df.empty:
        district_list = sorted(df["district"].dropna().unique().tolist())
    else:
        district_list = []

    col3, col4, col5 = st.columns(3)
    with col3:
        district = st.selectbox(
            t("lbl_district"),
            [t("sel_district")] + district_list,
        )
    with col4:
        if district != t("sel_district"):
            # first try authoritative taluk list from districts.json
            taluk_list = districts_data.get("taluks", {}).get(district, []) if districts_data else []
            # fallback to CSV-derived taluks if authoritative data missing
            if (not taluk_list) and (not df.empty):
                taluk_list = sorted(df[df["district"] == district]["taluk"].dropna().unique().tolist())
        else:
            taluk_list = []
        taluk = st.selectbox(
            t("lbl_taluk"),
            [t("sel_taluk")] + taluk_list
        )
    with col5:
        if taluk != t("sel_taluk"):
            # get villages from authoritative mapping by taluk name
            village_list = districts_data.get("villages", {}).get(taluk, []) if districts_data else []
            # fallback to CSV-derived villages if authoritative data missing
            if (not village_list) and (not df.empty):
                village_list = sorted(df[df["taluk"] == taluk]["village"].dropna().unique().tolist())
        else:
            village_list = []
        village = st.selectbox(
            t("lbl_village"),
            [t("sel_village")] + village_list
        )

    col6, col7 = st.columns(2)
    with col6:
        survey_no = st.text_input(
            t("lbl_survey"),
            value=st.session_state.get("field_survey_no", ""),
            placeholder=t("ph_survey")
        )
    with col7:
        land_area = st.number_input(
            t("lbl_area"),
            min_value=0.01,
            max_value=9999.0,
            value=float(st.session_state.get("field_land_area", 1.0)),
            step=0.01
        )

    if mutation_type in ["Sale", "Gift", t("val_sale"), t("val_gift")]:
        st.markdown(f"<div class='section-header'>{t('sec_transaction')}</div>", unsafe_allow_html=True)
        col8, col9 = st.columns(2)
        with col8:
            seller_name = st.text_input(
                t("lbl_seller"),
                value=st.session_state.get("field_seller_name", ""),
                placeholder=t("ph_seller")
            )
        with col9:
            buyer_name = st.text_input(
                t("lbl_buyer"),
                value=st.session_state.get("field_buyer_name", ""),
                placeholder=t("ph_buyer")
            )
    else:
        seller_name = ""
        buyer_name = ""

    st.markdown(f"<div class='section-header'>{t('sec_docs')}</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        t("lbl_upload"),
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"]
    )
    uploaded_doc_names = [f.name for f in uploaded_files] if uploaded_files else []

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(t("btn_generate"), use_container_width=True):

        form_data = {
            "applicant_name": applicant_name,
            "aadhaar": aadhaar,
            "mobile": mobile,
            "survey_no": survey_no,
            "district": district if district != t("sel_district") else "",
            "taluk": taluk if taluk != t("sel_taluk") else "",
            "village": village if village != t("sel_village") else "",
            "land_area": land_area,
            "mutation_type": mutation_type,
            "seller_name": seller_name,
            "buyer_name": buyer_name,
            "uploaded_docs": uploaded_doc_names
        }

        validation = validate_form(form_data)

        if not validation["is_valid"]:
            st.markdown("<div class='error-box'>", unsafe_allow_html=True)
            st.markdown(t("msg_fix_errors"))
            for err in validation["errors"]:
                st.markdown(err)
            st.markdown("</div>", unsafe_allow_html=True)

        else:
            if validation["warnings"]:
                st.markdown("<div class='warning-box'>", unsafe_allow_html=True)
                for w in validation["warnings"]:
                    st.markdown(w)
                st.markdown("</div>", unsafe_allow_html=True)

            with st.spinner(t("msg_generating")):

                # Generate all content safely with fallback
                english_app = generate_application(form_data)
                if not english_app:
                    english_app = t("err_gen_failed")

                kannada_app = translate_to_kannada(form_data)
                
                checklist = generate_checklist(mutation_type, uploaded_doc_names)
                proc_info = get_processing_info(mutation_type)

                # Generate files
                docx_path = generate_docx(english_app, form_data)
                pdf_path = generate_pdf(form_data)

                # Safely read file bytes if files were generated successfully
                docx_bytes = None
                if docx_path and os.path.exists(docx_path):
                    try:
                        with open(docx_path, "rb") as f:
                            docx_bytes = f.read()
                    except Exception:
                        pass
                
                pdf_bytes = None
                if pdf_path and os.path.exists(pdf_path):
                    try:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                    except Exception:
                        pass

            st.markdown(f"""
            <div class='success-box'>
                <h3>{t('msg_success')}</h3>
                <p style='color:#aaa;'>{t('msg_success_desc')}</p>
            </div>
            """, unsafe_allow_html=True)

            tab1, tab2, tab3, tab4 = st.tabs([
                t("tab_en"),
                t("tab_kn"),
                t("tab_dl"),
                t("tab_checklist")
            ])

            with tab1:
                st.markdown(f"<div class='section-header'>{t('tab_en')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='app-text-box'>{english_app}</div>", unsafe_allow_html=True)

            with tab2:
                st.markdown(f"<div class='section-header'>{t('tab_kn')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='app-text-box'>{kannada_app}</div>", unsafe_allow_html=True)

            with tab3:
                st.markdown(f"<div class='section-header'>{t('dl_center')}</div>", unsafe_allow_html=True)

                dl1, dl2 = st.columns(2)

                with dl1:
                    st.markdown(f"""<div class='glass-card' style='text-align:center;'>
                        <div style='font-size:2.5em;'>📝</div>
                        <div style='color:#85c1e9; font-weight:600;'>{t('dl_en_title')}</div>
                    </div>""", unsafe_allow_html=True)
                    if english_app:
                        st.download_button(
                            t("dl_en_btn"),
                            data=english_app.encode('utf-8'),
                            file_name="mutation_application_english.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        st.button(t("dl_en_unavail"), disabled=True, use_container_width=True)

                with dl2:
                    st.markdown(f"""<div class='glass-card' style='text-align:center;'>
                        <div style='font-size:2.5em;'>🌐</div>
                        <div style='color:#85c1e9; font-weight:600;'>{t('dl_kn_title')}</div>
                    </div>""", unsafe_allow_html=True)
                    if kannada_app:
                        st.download_button(
                            t("dl_kn_btn"),
                            data=kannada_app.encode('utf-8'),
                            file_name="mutation_application_kannada.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                    else:
                        st.button(t("dl_kn_unavail"), disabled=True, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                dl3, dl4 = st.columns(2)

                with dl3:
                    st.markdown(f"""<div class='glass-card' style='text-align:center;'>
                        <div style='font-size:2.5em;'>📘</div>
                        <div style='color:#85c1e9; font-weight:600;'>{t('dl_docx_title')}</div>
                        <div style='color:#888; font-size:0.8em;'>{t('dl_docx_desc')}</div>
                    </div>""", unsafe_allow_html=True)
                    if docx_bytes:
                        st.download_button(
                            t("dl_docx_btn"),
                            data=docx_bytes,
                            file_name="mutation_application.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                    else:
                        st.button(t("dl_docx_unavail"), disabled=True, use_container_width=True)

                with dl4:
                    st.markdown(f"""<div class='glass-card' style='text-align:center;'>
                        <div style='font-size:2.5em;'>📕</div>
                        <div style='color:#85c1e9; font-weight:600;'>{t('dl_pdf_title')}</div>
                        <div style='color:#888; font-size:0.8em;'>{t('dl_pdf_desc')}</div>
                    </div>""", unsafe_allow_html=True)
                    if pdf_bytes:
                        st.download_button(
                            t("dl_pdf_btn"),
                            data=pdf_bytes,
                            file_name="mutation_application.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.button(t("dl_pdf_unavail"), disabled=True, use_container_width=True)

            # Checklist Tab
            with tab4:
                st.markdown(f"<div class='section-header'>{t('chk_title')}</div>", unsafe_allow_html=True)

                # Show processing info
                proc_days = proc_info.get('processing_days', 0)
                authority = proc_info.get('authority', '')
                st.markdown(f"<div style='margin-bottom:8px; color:#666;'>{t('chk_processing_time')}: <strong>{proc_days} days</strong> • {t('chk_authority')}: <strong>{authority}</strong></div>", unsafe_allow_html=True)

                # Completion progress
                percent = checklist.get('completion_percent', 0)
                st.progress(percent)
                st.markdown(f"**{t('chk_completion')}:** {percent}%")

                # Show uploaded / missing documents in two columns
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**{t('chk_present')}**")
                    present = checklist.get('present', [])
                    if present:
                        for d in present:
                            st.markdown(f"- ✅ {d}")
                    else:
                        # If no uploaded docs, show a warning
                        if not uploaded_doc_names:
                            st.warning(t('chk_no_docs_uploaded'))
                        else:
                            st.markdown("- —")

                with c2:
                    st.markdown(f"**{t('chk_missing')}**")
                    missing = checklist.get('missing', [])
                    if missing:
                        for d in missing:
                            st.markdown(f"- ❌ {d}")
                    else:
                        st.markdown("- All documents present ✅")

                # Expandable required documents list
                with st.expander(t('chk_required')):
                    for d in checklist.get('required', []):
                        st.markdown(f"- {d}")

# ════════════════════════════════════════
# PAGE: DATASET EXPLORER
# ════════════════════════════════════════
elif page_labels[page] == "dataset":

    st.markdown(f"""
    <div class='hero-banner' style='padding:25px;'>
        <div style='font-size:1.8em; font-weight:700; color:white;'>{t('exp_hero_title')}</div>
        <div style='color:#85c1e9; margin-top:5px;'>{t('exp_hero_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.error(t("exp_err"))
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_district = st.selectbox(t("exp_filt_district"), [t("exp_all")] + sorted(df["district"].unique().tolist()))
        with col2:
            filter_mutation = st.selectbox(t("exp_filt_mutation"), [t("exp_all")] + df["mutation_type"].unique().tolist())
        with col3:
            filter_status = st.selectbox(t("exp_filt_status"), [t("exp_all")] + df["mutation_status"].unique().tolist())

        filtered = df.copy()
        if filter_district != t("exp_all"):
            filtered = filtered[filtered["district"] == filter_district]
        if filter_mutation != t("exp_all"):
            filtered = filtered[filtered["mutation_type"] == filter_mutation]
        if filter_status != t("exp_all"):
            filtered = filtered[filtered["mutation_status"] == filter_status]

        st.markdown(t("exp_showing", len(filtered)))
        st.dataframe(filtered.head(100), use_container_width=True, hide_index=True)

# ════════════════════════════════════════
# PAGE: FAQ
# ════════════════════════════════════════
elif page_labels[page] == "faq":

    st.markdown(f"""
    <div class='hero-banner' style='padding:25px;'>
        <div style='font-size:1.8em; font-weight:700; color:white;'>{t('faq_hero_title')}</div>
        <div style='color:#85c1e9; margin-top:5px;'>{t('faq_hero_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    if not faq_df.empty:
        for _, row in faq_df.iterrows():
            st.markdown(f"""
            <div class='faq-card'>
                <div class='faq-question'>❓ {row['question']}</div>
                <div class='faq-answer'>💡 {row['answer']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info(t("faq_err"))

# ── Footer ──
st.markdown(f"""
<div class='custom-footer'>
    {t('footer_text')}
</div>
""", unsafe_allow_html=True)