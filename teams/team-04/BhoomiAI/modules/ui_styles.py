# modules/ui_styles.py
# Premium Custom CSS Styles for Hackathon-Winning Quality

def get_custom_css():
    return """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@400;500&display=swap');

/* ── Global Reset & Typography ── */
* { 
    font-family: 'Outfit', 'Inter', sans-serif; 
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ── Main Background ── */
.stApp {
    background: linear-gradient(135deg, #090e17 0%, #111a28 50%, #060b13 100%);
    min-height: 100vh;
}

/* ── Hide Streamlit Defaults ── */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(10, 15, 25, 0.8) !important;
    backdrop-filter: blur(20px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.05); }

/* ── Animated Hero Banner ── */
.hero-banner {
    background: linear-gradient(-45deg, #0a192f, #112240, #1d3557, #0f2027);
    background-size: 400% 400%;
    animation: gradientHero 15s ease infinite;
    border-radius: 24px;
    padding: 50px 40px;
    text-align: center;
    margin-bottom: 40px;
    border: 1px solid rgba(100, 255, 218, 0.1);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255,255,255,0.1);
    position: relative;
    overflow: hidden;
}

@keyframes gradientHero {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(100, 255, 218, 0.05) 0%, transparent 60%);
    animation: pulseGlow 4s ease-in-out infinite;
}

@keyframes pulseGlow {
    0%, 100% { transform: scale(1); opacity: 0.6; }
    50% { transform: scale(1.1); opacity: 1; }
}

.hero-title {
    font-size: clamp(2em, 5vw, 3.5em);
    font-weight: 700;
    background: linear-gradient(to right, #ffffff, #a8b2d1);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
    letter-spacing: -1px;
}
.hero-subtitle {
    font-size: clamp(1em, 2vw, 1.2em);
    color: #8892b0;
    margin-top: 15px;
    font-weight: 400;
}
.hero-badge {
    display: inline-block;
    background: rgba(100, 255, 218, 0.1);
    border: 1px solid rgba(100, 255, 218, 0.3);
    color: #64ffda;
    padding: 6px 18px;
    border-radius: 30px;
    font-size: 0.85em;
    font-weight: 500;
    margin-top: 25px;
    backdrop-filter: blur(5px);
    box-shadow: 0 0 15px rgba(100,255,218,0.1);
}

/* ── Premium Glass Cards ── */
.glass-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 30px;
    border: 1px solid rgba(255,255,255,0.05);
    margin-bottom: 24px;
    box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.glass-card:hover {
    transform: translateY(-5px);
    border-color: rgba(100, 255, 218, 0.2);
    box-shadow: 0 20px 40px -10px rgba(0,0,0,0.7), 0 0 20px rgba(100,255,218,0.05);
}
.glass-card h3 {
    margin-top: 0;
    color: #e2e8f0;
    font-weight: 600;
    font-size: 1.3em;
}

/* ── Modern Metric Cards ── */
.metric-card {
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.3), rgba(17, 24, 39, 0.5));
    border-radius: 16px;
    padding: 24px;
    text-align: center;
    border: 1px solid rgba(59, 130, 246, 0.2);
    box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0; left: 0;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, transparent 50%);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.metric-card:hover { 
    transform: translateY(-8px) scale(1.02);
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 15px 30px rgba(37, 99, 235, 0.2);
}
.metric-card:hover::after { opacity: 1; }
.metric-value {
    font-size: 2.5em;
    font-weight: 700;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.metric-label {
    font-size: 0.9em;
    color: #94a3b8;
    margin-top: 8px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Section Headers ── */
.section-header {
    font-size: 1.5em;
    font-weight: 600;
    color: #f8fafc;
    border-left: 4px solid #3b82f6;
    padding-left: 16px;
    margin: 30px 0 20px 0;
    display: flex;
    align-items: center;
}

/* ── Status Boxes ── */
.success-box, .error-box, .warning-box {
    border-radius: 16px;
    padding: 24px;
    margin: 20px 0;
    backdrop-filter: blur(10px);
    animation: slideIn 0.5s ease-out;
}
@keyframes slideIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
.success-box {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 78, 59, 0.3));
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-left: 5px solid #10b981;
}
.error-box {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(127, 29, 29, 0.3));
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-left: 5px solid #ef4444;
}
.warning-box {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(120, 53, 15, 0.3));
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-left: 5px solid #f59e0b;
}

/* ── Checklist Items ── */
.checklist-item-done, .checklist-item-missing {
    padding: 12px 20px;
    border-radius: 12px;
    margin: 8px 0;
    font-weight: 500;
    backdrop-filter: blur(5px);
    transition: transform 0.2s ease;
}
.checklist-item-done:hover, .checklist-item-missing:hover {
    transform: translateX(5px);
}
.checklist-item-done {
    background: rgba(16, 185, 129, 0.05);
    border: 1px solid rgba(16, 185, 129, 0.2);
    color: #34d399;
}
.checklist-item-missing {
    background: rgba(239, 68, 68, 0.05);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #f87171;
}

/* ── Streamlit Buttons Overrides ── */
.stButton > button {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    font-weight: 600 !important;
    font-size: 1.05em !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 10px 20px -10px rgba(37, 99, 235, 0.5) !important;
}
.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 25px -10px rgba(37, 99, 235, 0.8) !important;
    border-color: rgba(255,255,255,0.3) !important;
}
.stButton > button:active {
    transform: translateY(1px) !important;
}

/* ── Input Fields ── */
.stTextInput > div > div > input,
.stNumberInput > div > div > input {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    padding: 10px 16px !important;
    transition: all 0.3s ease !important;
    font-size: 1em !important;
}

.stSelectbox > div > div {
    background: rgba(15, 23, 42, 0.6) !important;
    border: 1px solid rgba(148, 163, 184, 0.2) !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}

.stSelectbox [data-baseweb="select"] * {
    color: #f1f5f9 !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:focus-within,
.stNumberInput > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2) !important;
    background: rgba(15, 23, 42, 0.8) !important;
}

/* ── Tabs Styling ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(15, 23, 42, 0.4);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 8px;
    border: 1px solid rgba(255,255,255,0.05);
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    color: #94a3b8 !important;
    border-radius: 10px !important;
    padding: 12px 24px !important;
    font-weight: 500 !important;
    transition: all 0.3s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #e2e8f0 !important;
    background: rgba(255,255,255,0.05) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
}

/* ── Animated Progress Bar ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6) !important;
    background-size: 200% 100% !important;
    animation: shimmerProgress 2s infinite linear !important;
    border-radius: 10px !important;
}
@keyframes shimmerProgress {
    0% { background-position: 100% 0; }
    100% { background-position: -100% 0; }
}

/* ── Download Center Buttons ── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    padding: 14px 24px !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 10px 20px -10px rgba(16, 185, 129, 0.5) !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 15px 25px -10px rgba(16, 185, 129, 0.8) !important;
    border-color: rgba(255,255,255,0.3) !important;
}
.stDownloadButton > button:active {
    transform: translateY(1px) !important;
}

/* ── Disabled Button Style (for our fallbacks) ── */
button[disabled] {
    background: rgba(255,255,255,0.05) !important;
    color: #64748b !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    box-shadow: none !important;
    cursor: not-allowed !important;
    transform: none !important;
}

/* ── Application Text Box ── */
.app-text-box {
    background: #0f172a;
    border: 1px solid rgba(59, 130, 246, 0.2);
    border-radius: 16px;
    padding: 24px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 0.9em;
    color: #e2e8f0;
    white-space: pre-wrap;
    max-height: 500px;
    overflow-y: auto;
    line-height: 1.7;
    box-shadow: inset 0 2px 15px rgba(0,0,0,0.3);
}
.app-text-box::-webkit-scrollbar {
    width: 8px;
}
.app-text-box::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.02);
    border-radius: 4px;
}
.app-text-box::-webkit-scrollbar-thumb {
    background: rgba(59, 130, 246, 0.3);
    border-radius: 4px;
}

/* ── FAQ Card ── */
.faq-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    border-radius: 16px;
    padding: 20px 24px;
    border-left: 4px solid #3b82f6;
    margin-bottom: 16px;
    border-top: 1px solid rgba(255,255,255,0.02);
    border-right: 1px solid rgba(255,255,255,0.02);
    border-bottom: 1px solid rgba(255,255,255,0.02);
    transition: transform 0.2s ease;
}
.faq-card:hover {
    transform: translateX(5px);
    background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
}
.faq-question { color: #f8fafc; font-weight: 600; font-size: 1.1em; }
.faq-answer { color: #94a3b8; font-size: 0.95em; margin-top: 8px; line-height: 1.6; }

/* ── Language Indicator (small pill) ── */
.lang-indicator {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 999px;
    background: linear-gradient(135deg, #06b6d4, #7c3aed);
    color: #fff;
    font-weight: 700;
    box-shadow: 0 8px 20px rgba(124,58,237,0.18);
    font-size: 0.95em;
}
.lang-switch-wrapper { display:flex; gap:8px; justify-content:center; margin:10px 0 18px 0; }

/* ── Custom Footer ── */
.custom-footer {
    text-align: center;
    padding: 30px;
    color: #64748b;
    font-size: 0.85em;
    border-top: 1px solid rgba(255,255,255,0.05);
    margin-top: 60px;
    background: linear-gradient(to top, rgba(15, 23, 42, 0.8), transparent);
}
</style>
"""