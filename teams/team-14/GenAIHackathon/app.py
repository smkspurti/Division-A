import streamlit as st
from groq import Groq
import json

from modules.idea_generator import generate_ideas
from modules.dataset_fetcher import fetch_github_trending, format_github_context
from modules.skill_gap import analyze_skill_gap
from modules.roadmap import generate_roadmap
from modules.risk_analyzer import analyze_risks
from modules.chatbot import chat_with_mentor
from utils.charts import feasibility_bar_chart, radar_chart, skill_gap_gauge, risk_pie_chart
from utils.pdf_export import generate_pdf

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="IdeaForge AI",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Theme state ───────────────────────────────────────────────────────────────
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

T = {
    "dark": {
        "bg":           "#0f0f1a",
        "sidebar_bg":   "#13131f",
        "card_bg":      "#1a1a2e",
        "card_bg2":     "#16213e",
        "border":       "#2a2a3e",
        "text":         "#e2e8f0",
        "muted":        "#94a3b8",
        "tag_text":     "#818cf8",
        "msg_bot":      "#e2e8f0",
        "input_bg":     "#1a1a2e",
        "input_text":   "#e2e8f0",
        "input_border": "#3a3a5e",
        "tab_inactive": "#94a3b8",
        "h_color":      "#e2e8f0",
        "label_color":  "#94a3b8",
    },
    "light": {
        "bg":           "#f8fafc",
        "sidebar_bg":   "#f1f5f9",
        "card_bg":      "#ffffff",
        "card_bg2":     "#eef2ff",
        "border":       "#e2e8f0",
        "text":         "#1e293b",
        "muted":        "#64748b",
        "tag_text":     "#4f46e5",
        "msg_bot":      "#1e293b",
        "input_bg":     "#ffffff",
        "input_text":   "#1e293b",
        "input_border": "#c7d2fe",
        "tab_inactive": "#64748b",
        "h_color":      "#1e293b",
        "label_color":  "#374151",
    },
}[st.session_state.theme]

# ── Theme-aware CSS ────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    /* ── Hide ONLY the theme switcher buttons, keep rest of toolbar ── */
    [data-testid="stBaseButton-headerNoPadding"] {{ display: none !important; }}
    [data-testid="stToolbarActionButtonIcon"] {{ display: none !important; }}
    button[aria-label="Light"],
    button[aria-label="Dark"],
    button[aria-label="System"] {{ display: none !important; }}
    /* Hide the Light/Dark/System radio group inside the menu */
    [data-testid="stMainMenuList"] > li:has(button[role="radio"]) {{ display: none !important; }}
    footer {{ visibility: hidden !important; }}

    /* ── Full page & main area background ── */
    html, body,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stAppViewContainer"] > .main > .block-container,
    .block-container,
    .stApp {{
        background-color: {T["bg"]} !important;
        color: {T["text"]} !important;
    }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] > div:first-child {{
        background-color: {T["sidebar_bg"]} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {T["text"]} !important;
    }}

    /* ── ALL text everywhere ── */
    * {{
        color: {T["text"]};
    }}
    p, span, div, li, td, th, label, small {{
        color: {T["text"]} !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: {T["h_color"]} !important;
    }}

    /* ── Inputs, textareas, selects ── */
    input, textarea, select,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea {{
        background-color: {T["input_bg"]} !important;
        color: {T["input_text"]} !important;
        border-color: {T["input_border"]} !important;
    }}
    [data-baseweb="select"] > div,
    [data-baseweb="select"] * {{
        background-color: {T["input_bg"]} !important;
        color: {T["input_text"]} !important;
    }}
    /* Dropdown popup list */
    [data-baseweb="popover"] div,
    [data-baseweb="popover"] li,
    [data-baseweb="popover"] span,
    [role="listbox"],
    [role="listbox"] *,
    [role="option"],
    [role="option"] span,
    ul[data-baseweb="menu"],
    ul[data-baseweb="menu"] li,
    ul[data-baseweb="menu"] li span {{
        background-color: {T["input_bg"]} !important;
        color: {T["input_text"]} !important;
    }}
    [role="option"]:hover,
    [role="option"]:hover span {{
        background-color: {T["border"]} !important;
        color: {T["input_text"]} !important;
    }}

    /* ── Labels ── */
    .stTextInput label, .stTextArea label,
    .stSelectbox label, .stRadio label,
    [data-testid="stWidgetLabel"] p {{
        color: {T["label_color"]} !important;
    }}

    /* ── Markdown text ── */
    .stMarkdown p, .stMarkdown li,
    .stMarkdown span, .stMarkdown div {{
        color: {T["text"]} !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {{
        color: {T["tab_inactive"]} !important;
        background: transparent !important;
    }}
    .stTabs [aria-selected="true"] {{
        color: #6366f1 !important;
        border-bottom-color: #6366f1 !important;
    }}
    [data-testid="stTabsContent"] {{
        background-color: {T["bg"]} !important;
    }}

    /* ── Buttons (only our theme buttons keep gradient) ── */
    div[data-testid="stButton"] > button {{
        background: linear-gradient(135deg, #6366f1, #22d3ee) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        padding: 0.6rem 1.4rem !important;
        transition: opacity 0.2s !important;
    }}
    div[data-testid="stButton"] > button:hover {{ opacity: 0.85 !important; }}

    /* ── Dividers ── */
    hr {{ border-color: {T["border"]} !important; }}
    [data-testid="stSeparator"] {{ background-color: {T["border"]} !important; }}

    /* ── Alerts / warnings ── */
    [data-testid="stAlert"] {{
        background-color: {T["card_bg"]} !important;
        color: {T["text"]} !important;
    }}

    /* ── Spinner ── */
    [data-testid="stSpinner"] * {{ color: {T["text"]} !important; }}

    /* ── Custom component classes ── */
    .main-title {{
        font-size: 2.8rem; font-weight: 800; text-align: center;
        background: linear-gradient(135deg, #6366f1, #22d3ee);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        padding: 0.5rem 0;
    }}
    .subtitle {{
        text-align: center; color: {T["muted"]} !important; font-size: 1rem;
        margin-bottom: 1.5rem;
    }}
    .metric-card {{
        background: {T["card_bg"]} !important; border: 1px solid {T["border"]};
        border-radius: 12px; padding: 1rem 1.2rem; margin: 0.4rem 0;
    }}
    .idea-card {{
        background: linear-gradient(135deg, {T["card_bg"]}, {T["card_bg2"]}) !important;
        border: 1px solid #6366f1; border-radius: 14px;
        padding: 1.2rem 1.4rem; margin: 0.8rem 0;
    }}
    .rank-badge {{
        display: inline-block; background: #6366f1 !important; color: white !important;
        border-radius: 50%; width: 28px; height: 28px;
        text-align: center; line-height: 28px; font-weight: bold;
        margin-right: 8px; font-size: 0.9rem;
    }}
    .score-pill {{
        display: inline-block; padding: 2px 10px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 600; margin: 2px;
    }}
    .score-green {{ background: rgba(34,197,94,0.15) !important; color: #16a34a !important; }}
    .score-blue  {{ background: rgba(99,102,241,0.15) !important; color: {T["tag_text"]} !important; }}
    .score-amber {{ background: rgba(245,158,11,0.15) !important; color: #d97706 !important; }}
    .risk-high   {{ color: #ef4444 !important; font-weight: 600; }}
    .risk-med    {{ color: #f59e0b !important; font-weight: 600; }}
    .risk-low    {{ color: #22c55e !important; font-weight: 600; }}
    .week-card {{
        background: {T["card_bg"]} !important; border-left: 3px solid #6366f1;
        border-radius: 0 10px 10px 0; padding: 0.8rem 1rem; margin: 0.5rem 0;
    }}
    .chatbox {{
        background: {T["card_bg"]} !important; border: 1px solid {T["border"]};
        border-radius: 12px; padding: 1rem; min-height: 200px; max-height: 340px;
        overflow-y: auto;
    }}
    .msg-user {{ text-align: right; color: #6366f1 !important; margin: 6px 0; }}
    .msg-bot  {{ text-align: left; color: {T["msg_bot"]} !important; margin: 6px 0; }}
    .tag {{
        display: inline-block; background: rgba(99,102,241,0.15) !important;
        color: {T["tag_text"]} !important; border-radius: 6px; padding: 2px 8px;
        font-size: 0.75rem; margin: 2px;
    }}
</style>
""", unsafe_allow_html=True)

# ── Groq client ───────────────────────────────────────────────────────────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Session state ─────────────────────────────────────────────────────────────
for key in ["ideas", "skill_gap", "roadmap", "risks", "chat_history", "generated"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "chat_history" else None
if "generated" not in st.session_state:
    st.session_state.generated = False

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔥 IdeaForge AI")
    st.markdown(f"<p style='color:{T['muted']};font-size:0.85rem'>Hackathon Project Generator</p>", unsafe_allow_html=True)

    # Theme toggle
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        if st.button("🌙 Dark" if st.session_state.theme == "light" else "🌙 Dark (on)", use_container_width=True):
            if st.session_state.theme != "dark":
                st.session_state.theme = "dark"
                st.rerun()
    with col_t2:
        if st.button("☀️ Light" if st.session_state.theme == "dark" else "☀️ Light (on)", use_container_width=True):
            if st.session_state.theme != "light":
                st.session_state.theme = "light"
                st.rerun()

    st.divider()
    st.markdown("### 👤 Student Profile")

    name     = st.text_input("Full Name", placeholder="e.g. Rithika")
    skills   = st.text_area("Your Skills", placeholder="Python, ML, Web Dev, SQL...", height=80)
    domain_options = ["AI/ML", "Healthcare", "Education", "Cyber Security", "IoT", "Finance", "Agriculture", "Environment", "Other (Custom)"]
    domain_select = st.selectbox("Domain", domain_options)
    if domain_select == "Other (Custom)":
        domain = st.text_input("Enter your custom domain", placeholder="e.g. Sports Tech, Legal Tech, Gaming...")
    else:
        domain = domain_select
    tools    = st.text_input("Available Tools", placeholder="VS Code, Streamlit, TensorFlow...")
    duration = st.text_input("Project Duration", placeholder="e.g. 3 days, 4 weeks, 2 months", value="4 weeks")

    st.divider()
    generate_btn = st.button("⚡ Generate My Ideas", use_container_width=True)

    if st.session_state.generated:
        st.success("✅ Ideas ready!")
        st.markdown(f"<p style='color:{T['muted']};font-size:0.8rem'>Domain: {domain} | Duration: {duration}</p>", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<p class="main-title">🔥 IdeaForge AI</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">From skills to startup-ready ideas — powered by Groq & LLaMA 3.3</p>', unsafe_allow_html=True)

# ── Generate ──────────────────────────────────────────────────────────────────
if generate_btn:
    if not name or not skills or not tools:
        st.warning("⚠️ Please fill in Name, Skills, and Tools before generating.")
    else:
        col1, col2, col3, col4 = st.columns(4)
        p1 = col1.empty(); p2 = col2.empty(); p3 = col3.empty(); p4 = col4.empty()

        # ── Prompt Chain Step 1: Fetch live GitHub trending data ─────────────
        p1.info("🌐 Fetching live GitHub data...")
        repos = fetch_github_trending(domain, max_repos=5)
        github_context = format_github_context(repos)
        if repos:
            st.session_state["github_repos"] = repos  # save for display

        # ── Prompt Chain Step 2: Inject GitHub context → LLaMA ideas ────────
        p1.info("💡 Generating ideas from live data...")
        try:
            st.session_state.ideas = generate_ideas(client, name, skills, domain, tools, duration, github_context)
        except Exception as e:
            st.error(f"Idea generation failed: {e}")
            st.stop()
        p1.success(f"✅ Ideas done ({len(repos)} repos fetched)")

        top = st.session_state.ideas["ideas"][0]
        p2.info("🔍 Analyzing skills...")
        try:
            st.session_state.skill_gap = analyze_skill_gap(client, skills, top["title"], top["tech_stack"])
        except Exception as e:
            st.session_state.skill_gap = {"has_skills": [], "missing_skills": [], "readiness_score": 50, "summary": "Analysis unavailable"}
        p2.success("✅ Skill gap done")

        p3.info("🗓 Building roadmap...")
        try:
            st.session_state.roadmap = generate_roadmap(client, top["title"], top["description"], skills, duration)
        except Exception as e:
            st.session_state.roadmap = {"weeks": []}
        p3.success("✅ Roadmap done")

        p4.info("⚠️ Analyzing risks...")
        try:
            st.session_state.risks = analyze_risks(client, top["title"], skills, tools, duration)
        except Exception as e:
            st.session_state.risks = {"overall_risk": "Medium", "risk_score": 50, "risks": [], "recommendations": []}
        p4.success("✅ Risks done")

        st.session_state.generated = True
        st.session_state.chat_history = []
        st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.generated and st.session_state.ideas:
    ideas_data = st.session_state.ideas
    top_idea   = ideas_data["ideas"][0]

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💡 Project Ideas", "📊 Analysis", "🗓 Roadmap", "⚠️ Risk", "🤖 AI Mentor"
    ])

    # ── Tab 1: Ideas ──────────────────────────────────────────────────────────
    with tab1:
        st.markdown(f"### 👋 Here are your top ideas, {name}!")

        # Show live GitHub data used in prompt chain
        repos = st.session_state.get("github_repos", [])
        if repos:
            with st.expander(f"🌐 Live GitHub Data Used (Prompt Chain Step 1) — {len(repos)} trending repos fetched"):
                for r in repos:
                    topics = ", ".join(r["topics"][:4]) if r["topics"] else r.get("language", "")
                    st.markdown(f"""
<div class="metric-card" style="padding:0.6rem 1rem;margin:4px 0">
  <a href="{r["url"]}" target="_blank" style="color:#22d3ee;font-weight:600">{r["name"]}</a>
  <span class="score-pill score-blue">⭐ {r["stars"]:,}</span>
  <p style="margin:4px 0;font-size:0.83rem">{r["description"][:150]}</p>
  <span style="font-size:0.75rem">{topics}</span>
</div>""", unsafe_allow_html=True)

        st.plotly_chart(feasibility_bar_chart(ideas_data["ideas"]), use_container_width=True)
        st.divider()

        for idea in ideas_data["ideas"]:
            complexity_color = {"Easy": "score-green", "Medium": "score-amber", "Hard": "risk-high"}.get(idea.get("complexity", "Medium"), "score-amber")
            st.markdown(f"""
<div class="idea-card">
  <span class="rank-badge">{idea['rank']}</span>
  <strong style="color:{T['text']};font-size:1.1rem">{idea['title']}</strong>
  <span class="score-pill score-green">⭐ {idea['overall_score']}/10</span>
  <span class="score-pill {complexity_color}">{idea.get('complexity','Medium')}</span>
  <p style="color:{T['muted']};margin:8px 0 6px">{idea['description']}</p>
  <div>
    <span class="score-pill score-blue">Feasibility {idea['feasibility_score']}</span>
    <span class="score-pill score-blue">Innovation {idea['innovation_score']}</span>
    <span class="score-pill score-blue">Impact {idea['impact_score']}</span>
  </div>
  <p style="margin:8px 0 4px;color:{T['muted']};font-size:0.85rem">
    <strong style="color:{T['tag_text']}">Tech Stack:</strong>
    {''.join(f'<span class="tag">{t}</span>' for t in idea['tech_stack'])}
  </p>
  <p style="margin:4px 0;color:{T['muted']};font-size:0.85rem">
    <strong style="color:{T['tag_text']}">Dataset:</strong>
    <a href="{idea.get('dataset_url','#')}" target="_blank" style="color:#22d3ee">{idea['dataset']}</a>
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Tab 2: Analysis ───────────────────────────────────────────────────────
    with tab2:
        sg = st.session_state.skill_gap
        if sg:
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.plotly_chart(skill_gap_gauge(sg.get("readiness_score", 50)), use_container_width=True)
                st.markdown(f"<p style='color:{T['muted']};text-align:center'>{sg.get('summary','')}</p>", unsafe_allow_html=True)
            with col_b:
                st.plotly_chart(radar_chart(top_idea), use_container_width=True)

            col_c, col_d = st.columns(2)
            with col_c:
                st.markdown("#### ✅ Skills You Have")
                for s in sg.get("has_skills", []):
                    st.markdown(f'<span class="tag score-green">✓ {s}</span>', unsafe_allow_html=True)
            with col_d:
                st.markdown("#### 📚 Skills to Learn")
                for ms in sg.get("missing_skills", []):
                    imp_color = {"High": "risk-high", "Medium": "score-amber", "Low": "score-green"}.get(ms.get("importance","Medium"), "score-amber")
                    st.markdown(f"""
<div class="metric-card" style="margin:4px 0">
  <strong style="color:{T['text']}">{ms['skill']}</strong>
  <span class="score-pill {imp_color}" style="font-size:0.72rem">{ms.get('importance','')}</span><br>
  <span style="color:{T['muted']};font-size:0.82rem">⏱ {ms.get('learn_in','')} &nbsp;|&nbsp;
  <a href="{ms.get('resource_url','#')}" target="_blank" style="color:#22d3ee">{ms.get('resource','Learn online')}</a></span>
</div>
""", unsafe_allow_html=True)

    # ── Tab 3: Roadmap ────────────────────────────────────────────────────────
    with tab3:
        rm = st.session_state.roadmap
        if rm and rm.get("weeks"):
            st.markdown(f"### 🗓 Roadmap: {rm.get('project', top_idea['title'])}")
            colors = ["#6366f1", "#22d3ee", "#f59e0b", "#22c55e", "#ef4444", "#a855f7", "#ec4899", "#14b8a6"]
            for i, week in enumerate(rm["weeks"]):
                color = colors[i % len(colors)]
                st.markdown(f"""
<div class="week-card" style="border-left-color:{color}">
  <strong style="color:{color}">Week {week['week']}: {week['title']}</strong>
  <p style="color:{T['muted']};margin:4px 0;font-size:0.88rem">{week.get('goal','')}</p>
  <ul style="color:{T['text']};font-size:0.85rem;margin:4px 0 4px 16px">
    {''.join(f"<li>{t}</li>" for t in week.get('tasks', []))}
  </ul>
  <p style="color:#22d3ee;font-size:0.82rem;margin:4px 0">
    🏁 <em>{week.get('deliverable','')}</em>
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Tab 4: Risk ───────────────────────────────────────────────────────────
    with tab4:
        risk_data = st.session_state.risks
        if risk_data:
            col_r1, col_r2 = st.columns([1, 1])
            with col_r1:
                overall = risk_data.get("overall_risk", "Medium")
                score   = risk_data.get("risk_score", 50)
                risk_col = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(overall, "#f59e0b")
                st.markdown(f"""
<div class="metric-card" style="text-align:center;padding:1.5rem">
  <p style="color:{T['muted']};margin:0">Overall Risk Level</p>
  <h1 style="color:{risk_col};margin:4px 0">{overall}</h1>
  <p style="color:{T['muted']};margin:0">Risk Score: {score}/100</p>
</div>
""", unsafe_allow_html=True)
                if risk_data.get("risks"):
                    st.plotly_chart(risk_pie_chart(risk_data["risks"]), use_container_width=True)
            with col_r2:
                st.markdown("#### ⚠️ Risk Details")
                for risk in risk_data.get("risks", []):
                    prob_col = {"High": "risk-high", "Medium": "risk-med", "Low": "risk-low"}.get(risk.get("probability","Medium"), "risk-med")
                    st.markdown(f"""
<div class="metric-card">
  <strong style="color:{T['text']}">[{risk.get('category','')}] {risk.get('risk','')}</strong><br>
  <span class="score-pill {prob_col}" style="font-size:0.72rem">
    Prob: {risk.get('probability','')}
  </span>
  <span class="score-pill score-amber" style="font-size:0.72rem">
    Impact: {risk.get('impact','')}
  </span>
  <p style="color:{T['muted']};font-size:0.83rem;margin:6px 0 0">
    🛡 {risk.get('mitigation','')}
  </p>
</div>
""", unsafe_allow_html=True)

            if risk_data.get("recommendations"):
                st.markdown("#### 💡 Recommendations")
                for rec in risk_data["recommendations"]:
                    st.markdown(f"<p style='color:#22d3ee'>→ {rec}</p>", unsafe_allow_html=True)

    # ── Tab 5: AI Mentor Chatbot ──────────────────────────────────────────────
    with tab5:
        st.markdown("### 🤖 Ask Your AI Mentor")
        st.markdown(f"<p style='color:{T['muted']}'>Ask anything about your project ideas, tech stack, implementation, or career advice.</p>", unsafe_allow_html=True)

        chat_html = ""
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f'<div class="msg-user">🧑 {msg["content"]}</div>'
            else:
                chat_html += f'<div class="msg-bot">🤖 {msg["content"]}</div>'

        st.markdown(f'<div class="chatbox">{chat_html}</div>', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input("Ask anything...", placeholder="Which idea should I pick? How do I start?")
            send_btn   = st.form_submit_button("Send 💬", use_container_width=True)

        if send_btn and user_input:
            ideas_context = json.dumps(ideas_data["ideas"][:2], indent=2)
            with st.spinner("AI Mentor is thinking..."):
                bot_reply = chat_with_mentor(client, user_input, ideas_context, st.session_state.chat_history)
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑 Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

    # ── PDF Export ────────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📄 Export Full Report")
    col_pdf1, col_pdf2 = st.columns([2, 1])
    with col_pdf1:
        st.markdown(f"<p style='color:{T['muted']}'>Download a professional PDF report with all ideas, skill gap analysis, roadmap, and risk assessment.</p>", unsafe_allow_html=True)
    with col_pdf2:
        if st.button("📥 Generate PDF Report", use_container_width=True):
            with st.spinner("Building your PDF..."):
                student_data = {"name": name, "skills": skills, "domain": domain, "tools": tools, "duration": duration}
                try:
                    pdf_bytes = generate_pdf(
                        student_data,
                        st.session_state.ideas,
                        st.session_state.skill_gap or {},
                        st.session_state.roadmap or {},
                        st.session_state.risks or {}
                    )
                    st.download_button(
                        label="⬇️ Download PDF",
                        data=pdf_bytes,
                        file_name=f"{name.replace(' ','_')}_IdeaForge_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"PDF generation failed: {e}")

else:
    # ── Landing state ─────────────────────────────────────────────────────────
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
<div class="metric-card" style="text-align:center;padding:1.5rem">
  <h2 style="color:#6366f1">💡</h2>
  <h4 style="color:{T['text']}">5 Ranked Ideas</h4>
  <p style="color:{T['muted']};font-size:0.85rem">AI generates tailored project ideas based on your unique skill set and domain</p>
</div>
""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
<div class="metric-card" style="text-align:center;padding:1.5rem">
  <h2 style="color:#22d3ee">📊</h2>
  <h4 style="color:{T['text']}">Deep Analysis</h4>
  <p style="color:{T['muted']};font-size:0.85rem">Skill gap analysis, feasibility scoring, risk assessment and visual dashboards</p>
</div>
""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
<div class="metric-card" style="text-align:center;padding:1.5rem">
  <h2 style="color:#f59e0b">🤖</h2>
  <h4 style="color:{T['text']}">AI Mentor Chat</h4>
  <p style="color:{T['muted']};font-size:0.85rem">Chat with your personal AI mentor to get advice on building your project</p>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div style="text-align:center;margin:2rem 0;padding:2rem;background:{T['card_bg']};border-radius:14px;border:1px dashed {T['border']}">
  <h3 style="color:#6366f1">👈 Fill your profile in the sidebar to get started</h3>
  <p style="color:{T['muted']}">Enter your name, skills, domain, tools and duration — then click Generate!</p>
</div>
""", unsafe_allow_html=True)
