"""
app.py — ClinMatch AI: Clinical Trial Eligibility Screener
A13 Hackathon Solution — Healthcare & Medical AI Domain
Run: python -m streamlit run app.py
"""

import os, sys, json, time, io
import streamlit as st
import pandas as pd
import google.genai as genai
from dotenv import load_dotenv
import PyPDF2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from engine.criterion_parser import parse_criteria
from engine.ehr_parser import extract_ehr_facts, summarize_facts
from engine.eligibility_matcher import match_criteria, compute_overall_eligibility
from engine.report_generator import generate_report

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ClinMatch AI — Clinical Trial Eligibility Screener",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* ─── Background ─── */
section[data-testid="stSidebar"] { border-right: 1px solid #e2e8f0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

/* ─── Hide defaults ─── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

/* ─── Top header bar ─── */
.top-header {
  border-radius: 12px;
  padding: 20px 28px;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(37, 99, 235, 0.05);
  border: 1px solid rgba(37, 99, 235, 0.2);
}
.top-header-left { display: flex; align-items: center; gap: 16px; }
.top-header-logo {
  width: 44px; height: 44px;
  background: linear-gradient(135deg, #2563eb, #7c3aed);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.3rem;
}
.top-header-title { font-size: 1.3rem; font-weight: 800; color: #0f172a; margin: 0; }
.top-header-sub { font-size: 0.78rem; color: #64748b; margin: 2px 0 0; }
.top-header-badge {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 0.72rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

/* ─── Stat boxes ─── */
.stat-grid { display: flex; gap: 12px; margin-bottom: 16px; }
.stat-box {
  flex: 1;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0,0,0,.05);
}
.stat-number { font-size: 1.9rem; font-weight: 800; line-height: 1; }
.stat-label { font-size: 0.72rem; color: #64748b; margin-top: 4px; font-weight: 500; }

/* ─── Overall status banner ─── */
.status-banner {
  border-radius: 10px;
  padding: 20px 24px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
}
.status-eligible   { background:#f0fdf4; border: 1.5px solid #16a34a; }
.status-ineligible { background:#fff1f2; border: 1.5px solid #dc2626; }
.status-review     { background:#fffbeb; border: 1.5px solid #d97706; }
.status-icon { font-size: 2rem; flex-shrink: 0; }
.status-title { font-size: 1.1rem; font-weight: 800; margin: 0 0 3px; }
.status-subtitle { font-size: 0.8rem; margin: 0; opacity: 0.8; }

/* ─── Decision row cards ─── */
.crit-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-left: 4px solid;
  border-radius: 8px;
  padding: 14px 16px;
  margin-bottom: 8px;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  transition: box-shadow .15s;
}
.crit-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,.08); }
.crit-match    { border-left-color: #16a34a; }
.crit-nomatch  { border-left-color: #dc2626; }
.crit-uncertain{ border-left-color: #d97706; }
.crit-badge {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  min-width: 90px;
  text-align: center;
}
.badge-match    { background:#dcfce7; color:#15803d; }
.badge-nomatch  { background:#fee2e2; color:#b91c1c; }
.badge-uncertain{ background:#fef3c7; color:#b45309; }
.type-pill {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.65rem;
  font-weight: 600;
  margin-right: 6px;
}
.pill-inc { background:#eff6ff; color:#1d4ed8; }
.pill-exc { background:#fff1f2; color:#be123c; }
.crit-id { font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#64748b; font-weight:600; }
.crit-desc { font-size:0.85rem; font-weight:600; color:#0f172a; margin:3px 0; }
.crit-rationale { font-size:0.78rem; color:#475569; line-height:1.55; }
.crit-missing { font-size:0.72rem; color:#92400e; margin-top:4px; }

/* ─── Confidence bar ─── */
.conf-wrap { flex-shrink:0; text-align:center; min-width:64px; }
.conf-pct { font-size:1.1rem; font-weight:800; }
.conf-label { font-size:0.6rem; color:#94a3b8; }
.conf-bar-bg { height:5px; background:#f1f5f9; border-radius:3px; margin-top:4px; }
.conf-bar-fill { height:5px; border-radius:3px; }

/* ─── Section divider ─── */
.sec-div {
  font-size:0.72rem; font-weight:700; text-transform:uppercase;
  letter-spacing:0.1em; color:#94a3b8;
  display:flex; align-items:center; gap:10px;
  margin: 18px 0 12px;
}
.sec-div::after { content:''; flex:1; height:1px; background:#e2e8f0; }



/* ─── Alerts / info boxes ─── */
.info-box {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.82rem;
  color: #0369a1;
}
.warn-box {
  background: #fffbeb;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.82rem;
  color: #92400e;
}
.success-box {
  background: #f0fdf4;
  border: 1px solid #86efac;
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 0.82rem;
  color: #166534;
}

/* ─── Empty state ─── */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}
.empty-state-icon { font-size: 3.5rem; margin-bottom: 16px; }
.empty-state-title { font-size: 1.1rem; font-weight: 700; color: #475569; margin-bottom: 8px; }
.empty-state-sub { font-size: 0.83rem; color: #94a3b8; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

def _pdf(f):
    r = PyPDF2.PdfReader(io.BytesIO(f.read()))
    return "\n".join(pg.extract_text() or "" for pg in r.pages)
def _client(key): return genai.Client(api_key=key)

def _decision_card(r):
    d = r.get("decision","Uncertain")
    css = {"Match":"crit-match","No Match":"crit-nomatch","Uncertain":"crit-uncertain"}.get(d,"crit-uncertain")
    badge_css = {"Match":"badge-match","No Match":"badge-nomatch","Uncertain":"badge-uncertain"}.get(d,"badge-uncertain")
    icon = {"Match":"✔","No Match":"✘","Uncertain":"??"}.get(d,"?")
    conf = r.get("confidence",0.5)
    conf_pct = int(conf*100)
    conf_c = "#16a34a" if conf>=0.7 else ("#d97706" if conf>=0.4 else "#dc2626")
    ctype = r.get("type","inclusion")
    pill = f'<span class="type-pill pill-inc">INCLUSION</span>' if ctype=="inclusion" else f'<span class="type-pill pill-exc">EXCLUSION</span>'
    missing = r.get("missing_data","")
    missing_html = f'<div class="crit-missing">⚠ Missing data: {missing}</div>' if missing and missing not in ("null","None",None,"") else ""
    return f"""
<div class="crit-card {css}">
  <div style="flex:1;min-width:0;">
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
      <span class="crit-id">{r.get("criterion_id","?")}</span>
      {pill}
      <span class="crit-badge {badge_css}">{icon} {d.upper()}</span>
    </div>
    <div class="crit-desc">{r.get("description","")}</div>
    <div class="crit-rationale">{r.get("rationale","")}</div>
    {missing_html}
  </div>
  <div class="conf-wrap">
    <div class="conf-pct" style="color:{conf_c};">{conf_pct}%</div>
    <div class="conf-label">Confidence</div>
    <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf_pct}%;background:{conf_c};"></div></div>
  </div>
</div>"""

# ── Session state ─────────────────────────────────────────────────────────────
for k,v in [("history",[]),("results",None),("overall",None),
            ("patient_facts",None),("criteria_list",None),("trial_name","")]:
    if k not in st.session_state: st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="padding:20px 4px 16px;border-bottom:1px solid #1e293b;margin-bottom:20px;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:40px;height:40px;background:linear-gradient(135deg,#2563eb,#7c3aed);
             border-radius:10px;display:flex;align-items:center;justify-content:center;
             font-size:1.2rem;flex-shrink:0;">🧬</div>
        <div>
          <div style="font-size:1rem;font-weight:800;">ClinMatch AI</div>
          <div style="font-size:0.68rem;">Clinical Eligibility Screener</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── API Key Section ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
         letter-spacing:0.08em;color:#475569;margin-bottom:10px;">
      🔑 API Configuration
    </div>
    """, unsafe_allow_html=True)

    api_key = st.text_input(
        "Gemini API Key",
        value=os.getenv("GEMINI_API_KEY",""),
        type="password",
        placeholder="Enter your Gemini API key...",
        label_visibility="collapsed",
        key="api_key_field"
    )

    if api_key:
        # Masked key display
        masked = api_key[:6] + "•" * 10 + api_key[-4:]
        st.markdown(f"""
        <div style="background:#0d2d1a;border:1px solid #14532d;border-radius:8px;
             padding:10px 12px;margin-top:6px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:#4ade80;font-size:0.75rem;">●</span>
            <span style="color:#86efac;font-size:0.75rem;font-weight:600;">Connected</span>
          </div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;
               color:#4ade80;margin-top:4px;">{masked}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#1c1008;border:1px solid #78350f;border-radius:8px;
             padding:10px 12px;margin-top:6px;">
          <div style="display:flex;align-items:center;gap:8px;">
            <span style="color:#f59e0b;font-size:0.75rem;">●</span>
            <span style="color:#fbbf24;font-size:0.75rem;font-weight:600;">No API Key</span>
          </div>
          <div style="font-size:0.68rem;color:#78350f;margin-top:3px;">
            Get a free key at ai.google.dev
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
         letter-spacing:0.08em;color:#475569;margin-bottom:10px;">
      ⚙️ Display Options
    </div>
    """, unsafe_allow_html=True)
    show_facts = st.checkbox("Show extracted EHR facts", value=True, key="show_facts")
    show_json  = st.checkbox("Show raw JSON output",    value=False, key="show_json")

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="border-top:1px solid #1e293b;padding-top:16px;">
      <div style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
           letter-spacing:0.08em;color:#475569;margin-bottom:12px;">ℹ️ System Info</div>
      <div style="font-size:0.72rem;color:#64748b;line-height:1.9;">
        <div>🤖 <b style="color:#94a3b8;">Model:</b> Gemini 2.5 Flash</div>
        <div>🔗 <b style="color:#94a3b8;">Framework:</b> LangChain + Streamlit</div>
        <div>📄 <b style="color:#94a3b8;">Export:</b> DOCX + CSV</div>
        <div>🗂 <b style="color:#94a3b8;">Dataset:</b> ClinicalTrials.gov</div>
        <div style="margin-top:10px;padding-top:10px;border-top:1px solid #1e293b;">
          <span style="background:#312e81;color:#a5b4fc;padding:3px 8px;border-radius:4px;
                font-size:0.65rem;font-weight:700;">A13 · Healthcare & Medical AI</span>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# HEADER BAR
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="top-header">
  <div class="top-header-left">
    <div class="top-header-logo">🧬</div>
    <div>
      <div class="top-header-title">ClinMatch AI</div>
      <div class="top-header-sub">Clinical Trial Eligibility Screener — Powered by Generative AI</div>
    </div>
  </div>
  <span class="top-header-badge">A13 · Healthcare &amp; Medical AI · Gemini 2.5 Flash</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔍  Eligibility Screener", "📋  Session History", "ℹ️  About"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SCREENER
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: INPUTS ──────────────────────────────────────────────────────────
    with left:
        # EHR input
        with st.container(border=True):
            st.markdown('**👤 Patient EHR Input**')
            ehr_pdf = st.file_uploader("Upload Patient EHR (PDF)", type=["pdf"], key="ehr_pdf")
            ehr_text = _pdf(ehr_pdf) if ehr_pdf else ""

        # Trial input
        with st.container(border=True):
            st.markdown('**🧪 Clinical Trial Criteria**')
            trial_pdf = st.file_uploader("Upload Trial Criteria (PDF)", type=["pdf"], key="trial_pdf")
            trial_text = _pdf(trial_pdf) if trial_pdf else ""
            trial_name = trial_pdf.name if trial_pdf else "Trial"

        # Buttons
        c1, c2 = st.columns([4, 1])
        with c1:
            run = st.button("🚀  Run Eligibility Screening", use_container_width=True,
                            type="primary", key="run_btn")
        with c2:
            if st.button("Clear", use_container_width=True, key="clear_btn"):
                for k in ["results","overall","patient_facts","criteria_list"]:
                    st.session_state[k] = None
                st.rerun()

    # ── RIGHT: RESULTS ────────────────────────────────────────────────────────
    with right:
        # ── Run ───────────────────────────────────────────────────────────────
        if run:
            if not api_key:
                st.markdown('<div class="warn-box">⚠️ Please enter your Gemini API key in the sidebar.</div>',
                            unsafe_allow_html=True)
            elif not ehr_text.strip():
                st.markdown('<div class="warn-box">⚠️ Please provide patient EHR text.</div>',
                            unsafe_allow_html=True)
            elif not trial_text.strip():
                st.markdown('<div class="warn-box">⚠️ Please provide trial eligibility criteria.</div>',
                            unsafe_allow_html=True)
            else:
                try:
                    client = _client(api_key)
                    prog = st.empty()

                    prog.markdown("""<div class="info-box">🔬 Step 1 / 3 — Extracting patient clinical facts from EHR…</div>""", unsafe_allow_html=True)
                    pf = extract_ehr_facts(ehr_text, client)
                    if pf and isinstance(pf.get("primary_diagnoses"), list) and len(pf["primary_diagnoses"]) > 0:
                        if "FATAL PARSING ERROR" in str(pf["primary_diagnoses"][0]):
                            st.error(f"EHR Parsing Failed: {pf['primary_diagnoses'][0]}")
                            st.stop()

                    prog.markdown("""<div class="info-box">📑 Step 2 / 3 — Parsing trial eligibility criteria…</div>""", unsafe_allow_html=True)
                    cl = parse_criteria(trial_text, client)
                    if cl and len(cl) > 0 and "FATAL PARSING ERROR" in str(cl[0].get("description", "")):
                        st.error(f"Trial Parsing Failed: {cl[0].get('description')}")
                        st.stop()

                    prog.markdown(f"""<div class="info-box">⚖️ Step 3 / 3 — Evaluating {len(cl)} criteria against patient profile…</div>""", unsafe_allow_html=True)
                    res = match_criteria(pf, cl, client)
                    ov  = compute_overall_eligibility(res)
                    prog.empty()

                    st.session_state.results = res
                    st.session_state.overall = ov
                    st.session_state.patient_facts = pf
                    st.session_state.criteria_list = cl
                    st.session_state.trial_name = trial_name
                    st.session_state.history.append({
                        "Time":         time.strftime("%H:%M:%S"),
                        "Patient":      pf.get("patient_id","—"),
                        "Trial":        trial_name[:40],
                        "Status":       ov.get("overall_status",""),
                        "Criteria":     ov.get("total_criteria",0),
                        "Match":        ov.get("matched",0),
                        "No Match":     ov.get("not_matched",0),
                        "Uncertain":    ov.get("uncertain",0),
                    })
                    st.markdown(f'<div class="success-box">✅ Screening complete — {len(res)} criteria evaluated.</div>',
                                unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    st.exception(e)

        # ── Display ───────────────────────────────────────────────────────────
        if st.session_state.results:
            res = st.session_state.results
            ov  = st.session_state.overall
            pf  = st.session_state.patient_facts

            status = ov.get("overall_status","FURTHER REVIEW NEEDED")
            s_cfg = {
                "POTENTIALLY ELIGIBLE":  ("status-eligible",  "✅", "#15803d", "#dcfce7"),
                "NOT ELIGIBLE":          ("status-ineligible", "❌", "#b91c1c", "#fee2e2"),
                "FURTHER REVIEW NEEDED": ("status-review",    "⚠️", "#92400e", "#fef3c7"),
            }.get(status, ("status-review","⚠️","#92400e","#fef3c7"))

            # Overall banner
            st.markdown(f"""
            <div class="status-banner {s_cfg[0]}">
              <div class="status-icon">{s_cfg[1]}</div>
              <div>
                <div class="status-title" style="color:{s_cfg[2]};">{status}</div>
                <div class="status-subtitle" style="color:{s_cfg[2]};">
                  {ov.get("reason","")} &nbsp;·&nbsp; Avg. confidence {ov.get("avg_confidence",0):.0%}
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Stat boxes
            st.markdown(f"""
            <div class="stat-grid">
              <div class="stat-box">
                <div class="stat-number" style="color:#2563eb;">{ov.get("total_criteria",0)}</div>
                <div class="stat-label">Total Criteria</div>
              </div>
              <div class="stat-box">
                <div class="stat-number" style="color:#16a34a;">{ov.get("matched",0)}</div>
                <div class="stat-label">Matched</div>
              </div>
              <div class="stat-box">
                <div class="stat-number" style="color:#dc2626;">{ov.get("not_matched",0)}</div>
                <div class="stat-label">Not Matched</div>
              </div>
              <div class="stat-box">
                <div class="stat-number" style="color:#d97706;">{ov.get("uncertain",0)}</div>
                <div class="stat-label">Uncertain</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            def _sj(val):
                if not val: return "—"
                if isinstance(val, str): return val
                res = []
                for x in val:
                    if isinstance(x, dict):
                        # Extract the first value if it's a dict
                        res.append(str(list(x.values())[0]) if x else "")
                    else:
                        res.append(str(x))
                return ", ".join(res)

            # Patient facts expander
            if show_facts and pf:
                with st.expander("🏥 Extracted Patient Facts", expanded=False):
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"""
                        <div style="font-size:0.82rem;line-height:2;">
                          <b>ID:</b> {pf.get("patient_id","—")}<br>
                          <b>Age:</b> {pf.get("age","—")} &nbsp; <b>Sex:</b> {pf.get("sex","—")}<br>
                          <b>ECOG:</b> {pf.get("ecog_performance","—")}<br>
                          <b>Diagnoses:</b> {_sj(pf.get("primary_diagnoses"))}<br>
                          <b>Comorbidities:</b> {_sj(pf.get("comorbidities"))}
                        </div>""", unsafe_allow_html=True)
                    with col_b:
                        st.markdown(f"""
                        <div style="font-size:0.82rem;line-height:2;">
                          <b>Medications:</b> {_sj(pf.get("current_medications"))}<br>
                          <b>Biomarkers:</b> {_sj(pf.get("biomarkers"))}<br>
                          <b>Allergies:</b> {_sj(pf.get("allergies"))}<br>
                          <b>Prior Treatments:</b> {_sj(pf.get("prior_treatments"))}
                        </div>""", unsafe_allow_html=True)
                    if pf.get("lab_values"):
                        st.dataframe(
                            pd.DataFrame([{"Test":k,"Value":v} for k,v in pf["lab_values"].items()]),
                            use_container_width=True, hide_index=True
                        )

            # Criterion cards
            st.markdown('<div class="sec-div">Criterion-Level Decisions</div>', unsafe_allow_html=True)

            f1, f2 = st.columns(2)
            with f1:
                ft = st.selectbox("Type filter",["All","Inclusion Only","Exclusion Only"],
                                  label_visibility="collapsed", key="ft")
            with f2:
                fd = st.selectbox("Decision filter",["All","Match","No Match","Uncertain"],
                                  label_visibility="collapsed", key="fd")

            for r in res:
                if ft=="Inclusion Only" and r.get("type")!="inclusion": continue
                if ft=="Exclusion Only" and r.get("type")!="exclusion": continue
                if fd!="All" and r.get("decision")!=fd: continue
                st.markdown(_decision_card(r), unsafe_allow_html=True)

            # Export
            st.markdown('<div class="sec-div">📥 Export Results</div>', unsafe_allow_html=True)
            e1, e2 = st.columns(2)
            with e1:
                try:
                    docx = generate_report(pf, st.session_state.trial_name, res, ov)
                    pid = pf.get("patient_id","patient").replace(" ","_")
                    st.download_button("📄  Download DOCX Report", data=docx,
                        file_name=f"eligibility_{pid}_{time.strftime('%Y%m%d_%H%M')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True, key="dl_docx", type="primary")
                except Exception as ex:
                    st.error(f"DOCX error: {ex}")
            with e2:
                df_csv = pd.DataFrame([{
                    "ID":r.get("criterion_id"),"Type":r.get("type"),
                    "Description":r.get("description"),"Decision":r.get("decision"),
                    "Confidence":f"{r.get('confidence',0):.0%}",
                    "Rationale":r.get("rationale"),"Missing":r.get("missing_data",""),
                } for r in res])
                st.download_button("📊  Download CSV Table",
                    data=df_csv.to_csv(index=False).encode(),
                    file_name=f"criteria_{time.strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True, key="dl_csv")

            if show_json:
                with st.expander("🔧 Raw JSON"):
                    st.json({"overall": ov, "results": res})

        else:
            with st.container(border=True):
                st.markdown("""
                <div class="empty-state">
                  <div class="empty-state-icon">🔬</div>
                  <div class="empty-state-title">Ready to Screen</div>
                  <div class="empty-state-sub">
                    Upload a Patient EHR PDF and a Clinical Trial Criteria PDF on the left,<br>
                    then click <b style="color: #2563eb;">Run Eligibility Screening</b> to begin.
                  </div>
                  <div style="margin-top:20px;display:flex;justify-content:center;gap:8px;flex-wrap:wrap;">
                    <span style="background:rgba(37,99,235,0.1);color:#2563eb;padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;">✅ Match / No Match / Uncertain</span>
                    <span style="background:rgba(37,99,235,0.1);color:#2563eb;padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;">📄 DOCX Report Export</span>
                    <span style="background:rgba(37,99,235,0.1);color:#2563eb;padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:600;">🧬 Gemini 2.5 Flash</span>
                  </div>
                  <div style="margin-top:20px;font-size:0.8rem;color:#d97706;background:#fffbeb;border:1px solid #fef3c7;padding:10px;border-radius:8px;display:inline-block;">
                    💡 <b>Note:</b> The "Download DOCX Report" button will appear right here after the screening completes!
                  </div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORY
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not st.session_state.history:
        st.markdown("""
        <div class="card">
          <div class="empty-state">
            <div class="empty-state-icon">📋</div>
            <div class="empty-state-title">No Screenings Yet</div>
            <div class="empty-state-sub">Run a screening in the Eligibility Screener tab to see results here.</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        h1, h2, h3 = st.columns(3)
        total = len(st.session_state.history)
        elig  = sum(1 for h in st.session_state.history if h["Status"]=="POTENTIALLY ELIGIBLE")
        nelig = sum(1 for h in st.session_state.history if h["Status"]=="NOT ELIGIBLE")
        h1.metric("Total Screenings", total)
        h2.metric("Potentially Eligible", elig)
        h3.metric("Not Eligible", nelig)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        hdf = pd.DataFrame(st.session_state.history)

        def _color(val):
            return {
                "POTENTIALLY ELIGIBLE": "background-color:#dcfce7;color:#15803d",
                "NOT ELIGIBLE":         "background-color:#fee2e2;color:#b91c1c",
                "FURTHER REVIEW NEEDED":"background-color:#fef3c7;color:#92400e",
            }.get(val,"")

        st.dataframe(
            hdf.style.map(_color, subset=["Status"]),
            use_container_width=True, hide_index=True
        )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ABOUT
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    c1, c2 = st.columns([2,1])
    with c1:
        st.markdown("""
        ## 🧬 ClinMatch AI

        **Problem A13** — Clinical Trial Eligibility Screener using NLP  
        **Domain** — Healthcare & Medical AI [CO3/CO4]

        Matching patients to clinical trials requires parsing complex inclusion/exclusion criteria written in dense medical prose. ClinMatch AI automates this process using a 4-stage LLM pipeline powered by **Google Gemini 2.5 Flash**.

        ### Pipeline Architecture
        | Stage | Module | Description |
        |-------|--------|-------------|
        | 1 | `ehr_parser.py` | Extract structured clinical facts from EHR text |
        | 2 | `criterion_parser.py` | Parse trial criteria into structured list |
        | 3 | `eligibility_matcher.py` | Per-criterion Match / No Match / Uncertain |
        | 4 | `report_generator.py` | Generate professional DOCX report |

        ### Decision Logic
        - **NOT ELIGIBLE** if any exclusion criterion is matched
        - **NOT ELIGIBLE** if any inclusion criterion is not met
        - **FURTHER REVIEW NEEDED** if >40% of criteria are uncertain
        - **POTENTIALLY ELIGIBLE** if all evaluable criteria pass

        ### Datasets Used
        - **ClinicalTrials.gov** — Trial eligibility criteria (public domain)
        - **MIMIC-III inspired** — Synthetic EHR summaries based on published structure
        """)
    with c2:
        st.markdown("""
        ### Tech Stack
        """)
        for item in [
            ("🤖","LLM","Gemini 2.5 Flash"),
            ("🖥","UI","Streamlit"),
            ("📄","Export","python-docx"),
            ("🔍","PDF","PyPDF2"),
            ("📊","Data","pandas"),
            ("🔗","SDK","google-genai"),
        ]:
            st.markdown(f"""
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                 padding:10px 14px;margin-bottom:8px;display:flex;align-items:center;gap:12px;">
              <span style="font-size:1.2rem;">{item[0]}</span>
              <div>
                <div style="font-size:0.7rem;color:#94a3b8;font-weight:600;">{item[1]}</div>
                <div style="font-size:0.85rem;font-weight:700;color:#0f172a;">{item[2]}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#1e1b4b;border-radius:8px;padding:14px;margin-top:8px;text-align:center;">
          <div style="color:#a5b4fc;font-size:0.7rem;font-weight:700;text-transform:uppercase;
               letter-spacing:0.08em;">Hackathon</div>
          <div style="color:#f1f5f9;font-size:1rem;font-weight:800;margin-top:4px;">A13 · CO3/CO4</div>
          <div style="color:#818cf8;font-size:0.72rem;margin-top:4px;">Healthcare & Medical AI</div>
        </div>
        """, unsafe_allow_html=True)
