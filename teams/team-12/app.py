# -*- coding: utf-8 -*-
import os
import json
import traceback
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import tempfile
import time

# Import custom modules
from utils import smart_load_csv, normalize_sentinels
from sample_data import generate_dirty_titanic, generate_dirty_adult, generate_dirty_rein, generate_dirty_openrefine
from profiler import profile_dataset, compare_profiles
from agent import CleaningAgent
from report_generator import generate_docx_report
from action_registry import get_action_python_code
from validation import TransformationVerifier
from persistence import SessionStore

# Setup Page Configuration
st.set_page_config(
    page_title="DataCleanAgent \u2014 Autonomous AI Data Quality System",
    page_icon="\U0001f9f9",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Dark Plotly Template Helper
# ============================================================
def get_dark_plotly_template():
    return dict(
        layout=dict(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='#12161F',
            font=dict(family='Space Grotesk, Inter, system-ui', color='#C8CDD5'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.06)', tickfont=dict(size=10)),
            yaxis=dict(gridcolor='rgba(255,255,255,0.04)', zerolinecolor='rgba(255,255,255,0.06)', tickfont=dict(size=10)),
            colorway=['#7C6BF0', '#00D4C8', '#F97794', '#0BE881', '#FFC048', '#FF7675', '#74B9FF', '#B48DF3'],
            margin=dict(l=16, r=16, t=32, b=16),
        )
    )

# ============================================================
# Inject Ultra-Premium Dark Glassmorphism CSS
# ============================================================
st.markdown("""
<div class="ambient-glow-1"></div>
<div class="ambient-glow-2"></div>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

    :root {
        --bg-primary: #07090e;
        --bg-surface: #0b0e14;
        --bg-card: #111520;
        --bg-elevated: #161c2b;
        --bg-hover: #1b2234;
        --border-subtle: rgba(255,255,255,0.05);
        --border-medium: rgba(255,255,255,0.09);
        --accent-purple: #8B5CF6;
        --accent-cyan: #06B6D4;
        --accent-pink: #EC4899;
        --accent-blue: #3B82F6;
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --text-muted: #64748b;
        --quality-green: #10B981;
        --quality-amber: #F59E0B;
        --quality-red: #EF4444;
        --glass-bg: rgba(17, 21, 32, 0.65);
        --glass-border: rgba(255,255,255,0.06);
    }

    /* ── Reset & Globals ── */
    *, *::before, *::after { box-sizing: border-box; }
    
    /* ── Cybergrid and Ambient Background ── */
    .main, .stApp {
        background-color: #07090e !important;
        background-image: 
            radial-gradient(circle at 50% 50%, #0d111d 0%, #07090e 100%),
            linear-gradient(rgba(255, 255, 255, 0.005) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.005) 1px, transparent 1px) !important;
        background-size: 100% 100%, 40px 40px, 40px 40px !important;
        color: var(--text-primary) !important;
        font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    }
    .main .block-container { 
        padding-top: 2rem !important; 
        max-width: 1400px !important; 
        position: relative !important;
        z-index: 1 !important;
    }

    /* ── Ambient Background Glows ── */
    .ambient-glow-1 {
        position: fixed;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, rgba(0,0,0,0) 70%);
        top: -150px;
        left: -150px;
        pointer-events: none;
        z-index: 0;
    }
    .ambient-glow-2 {
        position: fixed;
        width: 800px;
        height: 800px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.04) 0%, rgba(0,0,0,0) 70%);
        bottom: -200px;
        right: -200px;
        pointer-events: none;
        z-index: 0;
    }

    /* ── Hide Default Streamlit Chrome ── */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    div[data-testid="stHeader"] {background: transparent !important; border-bottom: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #05070a 0%, #0a0d14 100%) !important;
        border-right: 1px solid var(--border-subtle) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
        font-family: 'Outfit', system-ui, sans-serif !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%) !important;
        color: #FFF !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 10px 20px !important;
        letter-spacing: 0.03em;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.1);
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        box-shadow: 0 8px 24px rgba(139, 92, 246, 0.45), 0 0 15px rgba(139, 92, 246, 0.25) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div,
    [data-testid="stSidebar"] .stTextInput > div > div > input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 10px !important;
        transition: all 0.3s ease !important;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div:focus-within,
    [data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        border-color: var(--accent-purple) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.12) !important;
        background: var(--bg-elevated) !important;
    }

    /* ── Form Control Label Styling ── */
    .stSelectbox label, .stTextInput label, .stRadio label, .stFileUploader label, .stNumberInput label {
        color: var(--text-secondary) !important;
        font-family: 'Space Grotesk', system-ui, sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
        letter-spacing: 0.03em !important;
        margin-bottom: 8px !important;
        text-transform: uppercase !important;
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(17, 21, 32, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        border-radius: 20px !important;
        padding: 6px !important;
        gap: 6px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 8px 32px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.02);
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border-radius: 14px !important;
        font-family: 'Space Grotesk', system-ui, sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        letter-spacing: 0.02em;
        border-bottom: none !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 12px 24px !important;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.25) 0%, rgba(6, 182, 212, 0.2) 100%) !important;
        color: #FFF !important;
        border: 1px solid rgba(139, 92, 246, 0.4) !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: var(--text-primary) !important;
        background: rgba(255,255,255,0.03) !important;
    }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 28px !important; }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(24px) saturate(1.8) !important;
        -webkit-backdrop-filter: blur(24px) saturate(1.8) !important;
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 20px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05) !important;
        position: relative !important;
        overflow: hidden !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stMetric"]:hover {
        border-color: rgba(139, 92, 246, 0.25) !important;
        box-shadow: 0 15px 35px rgba(0,0,0,0.5), 0 0 15px rgba(139,92,246,0.1), inset 0 1px 1px rgba(255,255,255,0.1) !important;
        transform: translateY(-2px) !important;
    }
    [data-testid="stMetric"]::before {
        content: "" !important;
        position: absolute !important;
        top: 0 !important; left: 0 !important;
        width: 100% !important; height: 3px !important;
        background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan)) !important;
    }
    [data-testid="stMetric"] label { color: var(--text-secondary) !important; font-size: 0.8rem !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 500 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 700 !important; font-size: 1.8rem !important; }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] svg { display: none; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%) !important;
        color: #FFF !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        font-family: 'Outfit', system-ui, sans-serif !important;
        font-weight: 600 !important;
        padding: 11px 28px !important;
        letter-spacing: 0.03em;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.25), inset 0 1px 0 rgba(255,255,255,0.1) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover {
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.45), 0 0 15px rgba(139, 92, 246, 0.2), inset 0 1px 0 rgba(255,255,255,0.15) !important;
        transform: translateY(-2px) !important;
    }
    .stButton > button:active { transform: translateY(0); }
    
    .stDownloadButton > button {
        background: linear-gradient(135deg, var(--accent-cyan) 0%, var(--quality-green) 100%) !important;
        color: #07090e !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        font-family: 'Outfit', system-ui, sans-serif !important;
        box-shadow: 0 4px 15px rgba(6, 182, 212, 0.2), inset 0 1px 0 rgba(255,255,255,0.2) !important;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
        padding: 11px 28px !important;
    }
    .stDownloadButton > button:hover {
        box-shadow: 0 8px 30px rgba(6, 182, 212, 0.4), 0 0 15px rgba(6, 182, 212, 0.25), inset 0 1px 0 rgba(255,255,255,0.3) !important;
        transform: translateY(-2px) !important;
    }

    /* ── Inputs ── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-subtle) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        font-family: 'Outfit', system-ui, sans-serif !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput > div > div > input:hover,
    .stNumberInput > div > div > input:hover,
    .stSelectbox > div > div:hover {
        border-color: rgba(139, 92, 246, 0.25) !important;
        background: var(--bg-elevated) !important;
        box-shadow: 0 0 10px rgba(139, 92, 246, 0.05) !important;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div:focus-within {
        border-color: var(--accent-purple) !important;
        background: var(--bg-elevated) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15) !important;
    }
    .stRadio > div { color: var(--text-primary) !important; }
    .stRadio label span { color: var(--text-secondary) !important; }

    /* ── Slider Customization ── */
    div[data-role="stSlider"] [data-baseweb="slider"] > div { background-color: var(--border-medium) !important; }
    div[data-role="stSlider"] [data-baseweb="slider"] div[role="progressbar"] { background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan)) !important; }
    div[data-role="stSlider"] [data-baseweb="slider"] thumb { background-color: var(--accent-purple) !important; border: 2px solid #FFF !important; }

    /* ── Expanders ── */
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-subtle) !important;
        border-radius: 12px !important;
        font-family: 'Space Grotesk', system-ui, sans-serif !important;
        font-weight: 500;
        transition: all 0.25s ease !important;
    }
    .streamlit-expanderHeader:hover { 
        background: var(--bg-elevated) !important; 
        border-color: rgba(139,92,246,0.2) !important;
    }
    .streamlit-expanderContent {
        background: rgba(17, 21, 32, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--border-subtle) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
    }

    /* ── Glass Card System ── */
    .glass-card {
        background: var(--glass-bg) !important;
        backdrop-filter: blur(24px) saturate(1.8);
        -webkit-backdrop-filter: blur(24px) saturate(1.8);
        border: 1px solid var(--glass-border) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .glass-card:hover {
        border-color: rgba(139, 92, 246, 0.3) !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6), 0 0 15px rgba(139, 92, 246, 0.15), inset 0 1px 1px rgba(255, 255, 255, 0.1) !important;
        transform: translateY(-2px) !important;
    }

    /* ── Hacker CRT Console ── */
    .console-box {
        background: radial-gradient(circle at top left, #05080f 0%, #020407 100%) !important;
        border: 1px solid rgba(139, 92, 246, 0.18) !important;
        border-left: 4px solid var(--accent-purple) !important;
        border-radius: 0 0 14px 14px !important;
        font-family: 'JetBrains Mono', monospace !important;
        padding: 20px !important;
        min-height: 400px !important;
        max-height: 480px !important;
        overflow-y: auto !important;
        line-height: 1.8 !important;
        font-size: 0.82rem !important;
        color: #e2e8f0 !important;
        box-shadow: inset 0 4px 20px rgba(0,0,0,0.8), 0 10px 30px rgba(0,0,0,0.5) !important;
        position: relative !important;
    }
    .console-box::before {
        content: "" !important;
        position: absolute !important;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%) !important;
        background-size: 100% 4px !important;
        z-index: 10 !important;
        pointer-events: none !important;
    }
    .console-line { margin-bottom: 3px; white-space: pre-wrap; word-break: break-all; position: relative; z-index: 5; }
    .console-thought { color: var(--accent-cyan) !important; text-shadow: 0 0 8px rgba(6, 182, 212, 0.3) !important; }
    .console-code { color: var(--quality-amber) !important; background: rgba(245,158,11,0.06) !important; padding: 1px 6px; border-radius: 3.5px; border: 1px solid rgba(245,158,11,0.12); }
    .console-success { color: var(--quality-green) !important; text-shadow: 0 0 8px rgba(16, 185, 129, 0.3) !important; font-weight: 600; }
    .console-error { color: var(--quality-red) !important; text-shadow: 0 0 8px rgba(239, 68, 68, 0.3) !important; font-weight: 600; }
    .console-system { color: #C084FC !important; }
    .console-cursor { display: inline-block; width: 8px; height: 14px; background: var(--accent-purple); animation: blink-cursor 1s step-end infinite; vertical-align: text-bottom; margin-left: 4px; }
    @keyframes blink-cursor { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

    /* ── Image/Artwork Styling ── */
    [data-testid="stImage"] img {
        border-radius: 16px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.7), 0 0 40px rgba(139, 92, 246, 0.12) !important;
        transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    [data-testid="stImage"] img:hover {
        transform: scale(1.005) translateY(-2px) !important;
        border-color: rgba(139, 92, 246, 0.25) !important;
        box-shadow: 0 35px 60px -10px rgba(0,0,0,0.8), 0 0 50px rgba(139, 92, 246, 0.2) !important;
    }

    /* ── Badges ── */
    .badge {
        padding: 3px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.7rem;
        display: inline-block;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-family: 'Space Grotesk', system-ui;
    }
    .badge-high { background: rgba(239,68,68,0.12) !important; color: var(--quality-red) !important; border: 1px solid rgba(239,68,68,0.25) !important; }
    .badge-medium { background: rgba(245,158,11,0.12) !important; color: var(--quality-amber) !important; border: 1px solid rgba(245,158,11,0.25) !important; }
    .badge-low { background: rgba(148,163,184,0.12) !important; color: #94a3b8 !important; border: 1px solid rgba(148,163,184,0.2) !important; }
    .badge-success { background: rgba(16,185,129,0.12) !important; color: var(--quality-green) !important; border: 1px solid rgba(16,185,129,0.25) !important; }

    /* ── Stat Card ── */
    .stat-card {
        background: var(--glass-bg);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 14px 16px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .stat-card:hover { border-color: rgba(139,92,246,0.15); }

    /* ── Animated Gradient Title ── */
    @keyframes gradient-flow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .gradient-title {
        font-family: 'Space Grotesk', 'Outfit', system-ui, sans-serif !important;
        font-size: 4.2rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan), var(--accent-pink), var(--accent-blue), var(--accent-purple)) !important;
        background-size: 400% 400% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: gradient-flow 10s ease infinite !important;
        margin: 0;
        letter-spacing: -0.03em !important;
        line-height: 1.1 !important;
    }

    /* ── Pulse Ring for Score ── */
    @keyframes pulse-ring {
        0% { box-shadow: 0 0 0 0 rgba(139,92,246,0.25); }
        70% { box-shadow: 0 0 0 15px rgba(139,92,246,0); }
        100% { box-shadow: 0 0 0 0 rgba(139,92,246,0); }
    }
    .score-hero { animation: pulse-ring 2.5s ease infinite; }

    /* ── DataFrame ── */
    .stDataFrame, [data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden; }

    /* ── Misc ── */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent) !important;
        margin: 28px 0 !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 { color: var(--text-primary) !important; font-family: 'Space Grotesk', system-ui, sans-serif !important; }
    .stMarkdown p, .stMarkdown li { color: var(--text-secondary) !important; }
    .stAlert { border-radius: 12px !important; }
    .stProgress > div > div > div { background: linear-gradient(90deg, var(--accent-purple), var(--accent-cyan)) !important; border-radius: 6px !important; }

    /* ── Dimension Icon Circles ── */
    .dim-icon {
        width: 38px; height: 38px; border-radius: 10px;
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 1.1rem; flex-shrink: 0;
    }

    /* ── Section Header ── */
    .section-header {
        display: flex; align-items: center; gap: 12px;
        margin-bottom: 20px; padding-bottom: 12px;
        border-bottom: 1px solid var(--border-subtle);
    }
    .section-header h3 {
        margin: 0 !important; font-size: 1.15rem !important;
        font-weight: 700 !important; color: var(--text-primary) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: -0.01em !important;
    }
    .section-header .accent-dot {
        width: 8px; height: 8px; border-radius: 50%;
        flex-shrink: 0;
    }

    /* ── Popover/Select dropdown ── */
    [data-baseweb="popover"] { background: var(--bg-elevated) !important; border: 1px solid var(--border-subtle) !important; border-radius: 12px !important; }
    [data-baseweb="menu"] { background: var(--bg-elevated) !important; }
    [data-baseweb="menu"] li { color: var(--text-primary) !important; }
    [data-baseweb="menu"] li:hover { background: rgba(139,92,246,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Session State Initialization
# ============================================================
for key, default in {
    'df': None, 'raw_df': None, 'initial_profile': None, 'current_profile': None,
    'cleaned_df': None, 'comparison': None, 'action_log': [], 'agent_running': False,
    'console_lines': []
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if 'api_key_set' not in st.session_state:
    st.session_state.api_key_set = "GOOGLE_API_KEY" in os.environ

if 'session_store' not in st.session_state:
    st.session_state.session_store = SessionStore()
if 'session_id' not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

# ============================================================
# Helper: Score Color
# ============================================================
def score_color(val):
    if val > 90: return '#0BE881'
    if val > 70: return '#FFC048'
    return '#FF7675'

def dim_icon(name):
    icons = {
        'Completeness': '\U0001f4cb', 'Uniqueness': '\U0001f5c2\ufe0f', 'Validity': '\u2705',
        'Consistency': '\U0001f504', 'Accuracy': '\U0001f3af', 'Integrity': '\U0001f512'
    }
    return icons.get(name, '\U0001f4ca')

def dim_color(name):
    colors = {
        'Completeness': '#7C6BF0', 'Uniqueness': '#00D4C8', 'Validity': '#0BE881',
        'Consistency': '#F97794', 'Accuracy': '#FFC048', 'Integrity': '#5B8DEF'
    }
    return colors.get(name, '#7C6BF0')

# ============================================================
# Sidebar Controls
# ============================================================
st.sidebar.markdown('''
<div style="display: flex; flex-direction: column; align-items: center; padding: 20px 0 16px 0;">
    <div style="width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 20px rgba(139,92,246,0.3); border: 1px solid rgba(255,255,255,0.15); margin-bottom: 12px;">
        <span style="font-size: 1.5rem; color: #FFF; font-weight: 800; font-family: 'Space Grotesk';">D</span>
    </div>
    <h2 style="font-family: 'Space Grotesk', sans-serif; font-weight: 800; font-size: 1.3rem;
        background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0; letter-spacing: -0.02em; line-height: 1.1;">DataCleanAgent</h2>
    <p style="color: #8E9AA8; font-size: 0.7rem; margin: 6px 0 0 0; letter-spacing: 0.06em; text-transform: uppercase; font-family: 'Outfit'; font-weight: 600;">AI Data Intelligence Platform</p>
</div>
''', unsafe_allow_html=True)
st.sidebar.markdown("---")

# 1. API Key
st.sidebar.markdown('<p style="color: var(--text-primary); font-weight: 600; font-size: 0.82rem; margin-bottom: 4px;">\U0001f510 Gemini API</p>', unsafe_allow_html=True)
api_input = st.sidebar.text_input(
    "Google API Key:", type="password",
    value=os.environ.get("GOOGLE_API_KEY", ""),
    help="Free key from Google AI Studio", label_visibility="collapsed"
)

if api_input:
    os.environ["GOOGLE_API_KEY"] = api_input
    st.session_state.api_key_set = True
    st.sidebar.markdown('''
    <div style="display:flex; align-items:center; gap:8px; padding:7px 12px; background:rgba(11,232,129,0.08); border-radius:8px; border:1px solid rgba(11,232,129,0.18);">
        <div style="width:7px;height:7px;border-radius:50%;background:#0BE881;box-shadow:0 0 8px #0BE881;"></div>
        <span style="color:#0BE881; font-size:0.75rem; font-weight:600;">Connected</span>
    </div>
    ''', unsafe_allow_html=True)
else:
    st.session_state.api_key_set = False
    st.sidebar.markdown('''
    <div style="display:flex; align-items:center; gap:8px; padding:7px 12px; background:rgba(255,192,72,0.08); border-radius:8px; border:1px solid rgba(255,192,72,0.18);">
        <div style="width:7px;height:7px;border-radius:50%;background:#FFC048;box-shadow:0 0 8px #FFC048;"></div>
        <span style="color:#FFC048; font-size:0.75rem; font-weight:600;">Key Required</span>
    </div>
    ''', unsafe_allow_html=True)

st.sidebar.markdown("---")

# 1.5. Resume Session Section
if 'session_store' in st.session_state:
    sessions = st.session_state.session_store.get_all_sessions()
    if sessions:
        st.sidebar.markdown('<p style="color: var(--text-primary); font-weight: 600; font-size: 0.82rem; margin-bottom: 4px;">📂 Resume Session</p>', unsafe_allow_html=True)
        session_options = ["-- Select Session --"]
        session_map = {}
        for s in sessions:
            created_dt = s['created_at'].split('T')[0] + ' ' + s['created_at'].split('T')[1][:5]
            label = f"{s['original_filename']} ({created_dt})"
            session_options.append(label)
            session_map[label] = s
            
        selected_session = st.sidebar.selectbox("Select session to resume:", session_options, label_visibility="collapsed")
        if selected_session != "-- Select Session --":
            s_info = session_map[selected_session]
            sess_id = s_info['session_id']
            curr_step = s_info['current_step']
            
            if st.sidebar.button("📂 Load Session", use_container_width=True):
                try:
                    # Load snapshots
                    raw_df = st.session_state.session_store.load_dataframe_snapshot(sess_id, 0)
                    curr_df = st.session_state.session_store.load_dataframe_snapshot(sess_id, curr_step)
                    
                    # Fetch initial profile at step 0
                    with st.session_state.session_store._get_connection() as conn:
                        row = conn.execute("SELECT profile_json FROM profiles WHERE session_id = ? AND step = 0", (sess_id,)).fetchone()
                        init_profile = json.loads(row["profile_json"]) if row else profile_dataset(raw_df)
                        
                    # Restore session state
                    st.session_state.session_id = sess_id
                    st.session_state.raw_df = raw_df
                    st.session_state.df = curr_df.copy()
                    st.session_state.initial_profile = init_profile
                    
                    if curr_step == 0:
                        st.session_state.cleaned_df = None
                        st.session_state.comparison = None
                        st.session_state.action_log = []
                        st.session_state.current_profile = init_profile
                    else:
                        st.session_state.cleaned_df = curr_df.copy()
                        curr_profile = st.session_state.session_store.get_latest_profile(sess_id)
                        st.session_state.current_profile = curr_profile
                        st.session_state.comparison = compare_profiles(init_profile, curr_profile)
                        st.session_state.action_log = st.session_state.session_store.get_session_history(sess_id)
                        
                    st.session_state.console_lines = [
                        f"[SYSTEM] Resumed session: {s_info['original_filename']}",
                        f"[SYSTEM] Loaded step {curr_step} successfully."
                    ]
                    
                    st.sidebar.success("Session loaded!")
                    time.sleep(0.8)
                    st.rerun()
                except Exception as ex:
                    st.sidebar.error(f"Failed to load: {str(ex)}")
        st.sidebar.markdown("---")

# 2. Data Source
st.sidebar.markdown('<p style="color: var(--text-primary); font-weight: 600; font-size: 0.82rem; margin-bottom: 4px;">\U0001f4c1 Data Source</p>', unsafe_allow_html=True)
data_source = st.sidebar.selectbox(
    "Choose Data Ingestion Method:",
    [
        "Upload CSV File", 
        "Use Titanic Survival Dataset (Kaggle)", 
        "Use UCI Adult Income Dataset",
        "Use Dirty Data Challenge Dataset (REIN)",
        "Use OpenRefine Test Dataset",
        "Use Synthetic Messy Dataset"
    ],
    label_visibility="collapsed"
)

loaded_file = None
load_trigger = False

if data_source == "Upload CSV File":
    uploaded_file = st.sidebar.file_uploader("Upload CSV:", type=["csv"], label_visibility="collapsed")
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_file.getvalue())
            loaded_file = tmp.name
        load_trigger = True
else:
    if st.sidebar.button("\U0001f680 Load Dataset", type="primary", use_container_width=True):
        if data_source == "Use Titanic Survival Dataset (Kaggle)":
            loaded_file = "s:/GenAi_hackthon/data/titanic.csv"
            if not os.path.exists(loaded_file):
                st.sidebar.warning("Titanic CSV missing. Generating synthetic instead.")
                dirty_df = generate_dirty_titanic(250)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                    dirty_df.to_csv(tmp.name, index=False)
                    loaded_file = tmp.name
        elif data_source == "Use UCI Adult Income Dataset":
            dirty_df = generate_dirty_adult(500)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                dirty_df.to_csv(tmp.name, index=False)
                loaded_file = tmp.name
        elif data_source == "Use Dirty Data Challenge Dataset (REIN)":
            dirty_df = generate_dirty_rein(300)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                dirty_df.to_csv(tmp.name, index=False)
                loaded_file = tmp.name
        elif data_source == "Use OpenRefine Test Dataset":
            dirty_df = generate_dirty_openrefine(250)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                dirty_df.to_csv(tmp.name, index=False)
                loaded_file = tmp.name
        else:
            dirty_df = generate_dirty_titanic(200)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                dirty_df.to_csv(tmp.name, index=False)
                loaded_file = tmp.name
        load_trigger = True

# Ingestion Processing
if load_trigger and loaded_file:
    with st.spinner("Analyzing file structure..."):
        try:
            df, meta = smart_load_csv(loaded_file)
            profile = profile_dataset(df)
            
            # Setup session in SQLite store
            import uuid
            sess_id = str(uuid.uuid4())
            st.session_state.session_id = sess_id
            st.session_state.session_store.create_session(sess_id, os.path.basename(loaded_file))
            st.session_state.session_store.save_profile(sess_id, 0, profile)
            st.session_state.session_store.save_dataframe_snapshot(sess_id, 0, df)
            
            st.session_state.raw_df = df.copy()
            st.session_state.df = df.copy()
            st.session_state.initial_profile = profile
            st.session_state.current_profile = profile
            st.session_state.cleaned_df = None
            st.session_state.comparison = None
            st.session_state.action_log = []
            st.session_state.console_lines = [
                f"[SYSTEM] Dataset loaded \u2014 Encoding: {meta['encoding']}, Delimiter: '{meta['delimiter']}', Shape: {meta['original_shape']}",
                f"[SYSTEM] Profiling complete \u2014 Quality Score: {profile['overall_score']:.1f}%"
            ]
            st.success("\u2705 Dataset ingested & profiled successfully!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.code(traceback.format_exc())

# Sidebar dataset stats
if st.session_state.df is not None:
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p style="color: var(--text-primary); font-weight: 600; font-size: 0.82rem; margin-bottom: 8px;">\U0001f4ca Dataset Overview</p>', unsafe_allow_html=True)

    _r, _c = st.session_state.df.shape
    _nulls = int(st.session_state.df.isna().sum().sum())
    _null_pct = (_nulls / st.session_state.df.size) * 100

    st.sidebar.markdown(f'''
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:8px;">
        <div class="stat-card" style="padding:10px;">
            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Rows</div>
            <div style="color:#7C6BF0; font-size:1.15rem; font-weight:700; margin-top:2px;">{_r:,}</div>
        </div>
        <div class="stat-card" style="padding:10px;">
            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Columns</div>
            <div style="color:#00D4C8; font-size:1.15rem; font-weight:700; margin-top:2px;">{_c}</div>
        </div>
    </div>
    <div class="stat-card" style="padding:10px;">
        <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Missing Cells</div>
        <div style="display:flex; align-items:baseline; gap:6px; margin-top:2px;">
            <span style="color:#F97794; font-size:1.15rem; font-weight:700;">{_nulls:,}</span>
            <span style="color:#8E9AA8; font-size:0.75rem;">({_null_pct:.1f}%)</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if st.session_state.current_profile:
        _s = st.session_state.current_profile['overall_score']
        _sc = score_color(_s)
        st.sidebar.markdown(f'''
        <div class="stat-card" style="padding:12px; margin-top:6px; border-left:3px solid {_sc};">
            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Quality Score</div>
            <div style="color:{_sc}; font-size:1.5rem; font-weight:800; margin-top:2px;">{_s:.1f}%</div>
            <div style="background:#1A1F2B; border-radius:4px; height:4px; overflow:hidden; margin-top:6px;">
                <div style="width:{_s}%; height:100%; background:linear-gradient(90deg, {_sc}, {_sc}88); border-radius:4px;"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

# ============================================================
# Main Content Area
# ============================================================

if st.session_state.df is None:
    # ── LANDING PAGE ──
    st.markdown('''
    <div style="text-align:center; padding: 80px 20px 20px 20px; position: relative;">
        <h1 class="gradient-title">DataCleanAgent</h1>
        <p style="color: #94a3b8; font-size: 1.1rem; font-family: 'Outfit'; margin-top: 8px; font-weight: 400;">
            Autonomous AI-Powered Data Quality Intelligence Platform
        </p>
        <div style="display:flex; justify-content:center; gap:32px; margin-top:24px;">
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:6px; height:6px; border-radius:50%; background:#7C6BF0;"></div>
                <span style="color:#94a3b8; font-size:0.78rem; font-family: 'Outfit'; font-weight: 500;">6-Dimension Profiling</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:6px; height:6px; border-radius:50%; background:#00D4C8;"></div>
                <span style="color:#94a3b8; font-size:0.78rem; font-family: 'Outfit'; font-weight: 500;">Gemini-Powered Agent</span>
            </div>
            <div style="display:flex; align-items:center; gap:6px;">
                <div style="width:6px; height:6px; border-radius:50%; background:#F97794;"></div>
                <span style="color:#94a3b8; font-size:0.78rem; font-family: 'Outfit'; font-weight: 500;">Audit Reports</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1.1, 1.8, 1.1])
    with col_m:
        st.image("data/hero.png", use_column_width=True)

    # Feature cards
    st.markdown('<div style="height:32px;"></div>', unsafe_allow_html=True)
    cols = st.columns(2)
    features = [
        ('\U0001f52c', 'Deep Profiling', 'Statistical analysis across 6 quality dimensions with IQR, Z-score, Isolation Forest outlier detection, and fuzzy string matching.', '#7C6BF0', 'ISO 25012-inspired'),
        ('\U0001f916', 'AI Cleaning Agent', 'Autonomous ReAct pipeline with self-healing code generation. Gemini analyzes issues, writes pandas transformations, validates results.', '#00D4C8', 'Powered by Gemini 2.5'),
        ('\U0001f4c4', 'Audit & Export', 'Professional DOCX reports with embedded charts, methodology sections, before/after tables, and complete action audit trails.', '#F97794', 'Enterprise-grade reports'),
    ]
    for col, (icon, title, desc, color, tag) in zip(cols, features):
        with col:
            st.markdown(f'''
            <div class="glass-card" style="text-align:center; border-top: 2px solid {color}; min-height: 260px; padding: 28px 20px;">
                <div style="width:52px; height:52px; border-radius:14px; background:{color}12; border:1px solid {color}25;
                    display:inline-flex; align-items:center; justify-content:center; font-size:1.6rem; margin-bottom:16px;">{icon}</div>
                <h3 style="color: var(--text-primary); font-family: 'Space Grotesk'; margin-bottom: 8px; font-size: 1.1rem; font-weight: 700;">{title}</h3>
                <p style="color: #94a3b8; font-size: 0.82rem; line-height: 1.55; margin-bottom: 12px; font-family: 'Outfit';">{desc}</p>
                <span style="background:{color}10; color:{color}; font-size:0.68rem; padding:3px 10px; border-radius:6px; border:1px solid {color}20; font-weight:600; letter-spacing:0.03em; font-family: 'Outfit';">{tag}</span>
            </div>
            ''', unsafe_allow_html=True)

    st.markdown('''
    <div style="text-align:center; padding: 40px 20px 10px 20px;">
        <div style="display:inline-flex; align-items:center; gap:8px; background:rgba(124,107,240,0.06); border:1px solid rgba(124,107,240,0.12); border-radius:10px; padding:10px 20px;">
            <span style="font-size:1.1rem;">👉</span>
            <span style="color:#94a3b8; font-size:0.85rem; font-family: 'Outfit'; font-weight: 500;">Load a dataset from the sidebar to begin</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

else:
    # ── PREMIUM APP HEADER ──
    st.markdown(f'''
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid rgba(255,255,255,0.06);">
        <div style="display:flex; align-items:center; gap:14px;">
            <div style="width: 42px; height: 42px; border-radius: 12px; background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan)); display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(139,92,246,0.3); border: 1px solid rgba(255,255,255,0.15);">
                <span style="font-size: 1.3rem; color: #FFF; font-weight: 800; font-family: 'Space Grotesk';">D</span>
            </div>
            <div>
                <h1 style="font-family:'Space Grotesk', sans-serif; font-weight:800; font-size:1.45rem; margin:0;
                    background: linear-gradient(135deg, var(--accent-purple), var(--accent-cyan));
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                    letter-spacing:-0.02em; line-height:1.2;">DataCleanAgent</h1>
                <p style="color:#64748b; font-size:0.75rem; margin:2px 0 0 0; font-family:'Outfit', sans-serif; font-weight:500; letter-spacing: 0.02em;">
                    Autonomous AI Data Restoration System
                </p>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:16px;">
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.05); padding:6px 14px; border-radius:10px; display:flex; align-items:center; gap:8px;">
                <div style="width:6px; height:6px; border-radius:50%; background:#10B981; box-shadow: 0 0 8px #10B981;"></div>
                <span style="color:#94a3b8; font-size:0.75rem; font-family:'Outfit', sans-serif; font-weight:600;">ACTIVE SESSION:</span>
                <span style="color:#fff; font-size:0.75rem; font-family:'JetBrains Mono'; font-weight:500;">{st.session_state.session_id[:8]}...</span>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # ── MAIN INTERFACE ──
    tab1, tab2, tab3, tab4 = st.tabs(["\U0001f4ca  Profile", "\U0001f916  Agent Console", "\U0001f4c8  Compare", "\U0001f4c4  Report & Audit"])

    # ============================================================
    # TAB 1: PROFILE
    # ============================================================
    with tab1:
        profile = st.session_state.initial_profile

        # A. Hero Score Card
        sv = profile['overall_score']
        sc = score_color(sv)
        st.markdown(f'''
        <div class="glass-card score-hero" style="text-align:center; border: 1px solid {sc}22; box-shadow: 0 0 40px {sc}10; margin-bottom: 28px; padding: 32px 20px;">
            <p style="color: #8E9AA8; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.12em; margin-bottom: 8px; font-weight: 600;">Overall Data Quality Score</p>
            <div style="font-size: 4.5rem; color: {sc}; font-family: 'Outfit'; font-weight: 900; margin: 0; line-height: 1; letter-spacing: -0.03em;">{sv:.1f}<span style="font-size:2rem; opacity:0.7;">%</span></div>
            <p style="color: #8E9AA8; font-size: 0.75rem; margin-top: 8px;">Weighted harmonic mean across 6 quality dimensions</p>
            <div style="max-width:300px; margin:12px auto 0 auto; background:#1A1F2B; border-radius:6px; height:6px; overflow:hidden;">
                <div style="width:{sv}%; height:100%; background:linear-gradient(90deg, {sc}, {sc}AA); border-radius:6px; transition: width 1s ease;"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        # B. 6 Dimension Cards + Radar
        col_dims, col_radar = st.columns([1.1, 0.9])

        with col_dims:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#7C6BF0;"></div>
                <h3>Quality Dimensions</h3>
            </div>''', unsafe_allow_html=True)

            dims = profile["dimension_scores"]
            dim_names = list(dims.keys())

            for row_start in range(0, len(dim_names), 2):
                row_cols = st.columns(2)
                for idx, col in enumerate(row_cols):
                    dim_idx = row_start + idx
                    if dim_idx < len(dim_names):
                        name = dim_names[dim_idx]
                        val = dims[name]
                        dc = dim_color(name)
                        di = dim_icon(name)
                        vc = score_color(val)
                        with col:
                            st.markdown(f'''
                            <div class="glass-card" style="padding:16px; margin-bottom:10px;">
                                <div style="display:flex; align-items:center; gap:10px; margin-bottom:10px;">
                                    <div class="dim-icon" style="background:{dc}12; border:1px solid {dc}25;">{di}</div>
                                    <div>
                                        <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">{name}</div>
                                        <div style="color:{vc}; font-size:1.6rem; font-weight:800; font-family:'Outfit'; line-height:1.1; margin-top:2px;">{val:.1f}%</div>
                                    </div>
                                </div>
                                <div style="background:#1A1F2B; border-radius:4px; height:5px; overflow:hidden;">
                                    <div style="width:{val}%; height:100%; background:linear-gradient(90deg, {dc}, {dc}88); border-radius:4px;"></div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)

        with col_radar:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#00D4C8;"></div>
                <h3>Quality Radar</h3>
            </div>''', unsafe_allow_html=True)

            categories = list(profile["dimension_scores"].keys())
            values = list(profile["dimension_scores"].values())

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=values + [values[0]],
                theta=categories + [categories[0]],
                fill='toself', name='Current',
                line=dict(color='#7C6BF0', width=2),
                fillcolor='rgba(124, 107, 240, 0.18)',
                marker=dict(size=6, color='#7C6BF0')
            ))
            fig_radar.update_layout(
                polar=dict(
                    bgcolor='rgba(0,0,0,0)',
                    radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=8, color='#8E9AA8'), gridcolor='rgba(255,255,255,0.04)', linecolor='rgba(255,255,255,0.04)'),
                    angularaxis=dict(tickfont=dict(size=10, color='#C8CDD5'), gridcolor='rgba(255,255,255,0.06)', linecolor='rgba(255,255,255,0.06)')
                ),
                showlegend=False, height=340,
                margin=dict(t=20, b=20, l=45, r=45),
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Outfit, system-ui', color='#C8CDD5')
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # C. Correlation Matrix
        corr_data = profile.get('correlation_matrix', {})
        if corr_data.get('matrix') and len(corr_data.get('columns', [])) >= 2:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#F97794;"></div>
                <h3>Correlation Matrix</h3>
            </div>''', unsafe_allow_html=True)

            fig_corr = go.Figure(data=go.Heatmap(
                z=corr_data['matrix'],
                x=corr_data['columns'],
                y=corr_data['columns'],
                colorscale=[[0, '#FF7675'], [0.5, '#0F1219'], [1, '#00D4C8']],
                zmin=-1, zmax=1,
                text=[[f'{v:.2f}' for v in row] for row in corr_data['matrix']],
                texttemplate='%{text}',
                textfont=dict(size=10, color='#C8CDD5'),
                hovertemplate='%{x} vs %{y}: %{z:.3f}<extra></extra>'
            ))
            corr_layout = get_dark_plotly_template()['layout'].copy()
            corr_layout['margin'] = dict(t=8, b=8, l=8, r=8)
            corr_layout['height'] = 380
            fig_corr.update_layout(**corr_layout)
            st.plotly_chart(fig_corr, use_container_width=True)

            # Strong correlations chips
            strong = corr_data.get('strong_correlations', [])
            if strong:
                chips_html = '<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:8px;">'
                for s in strong[:8]:
                    c = '#00D4C8' if s['correlation'] > 0 else '#FF7675'
                    chips_html += f'<span style="background:{c}0D; color:{c}; border:1px solid {c}20; padding:4px 10px; border-radius:6px; font-size:0.72rem; font-weight:600;">{s["col1"]} \u2194 {s["col2"]}: {s["correlation"]:.3f}</span>'
                chips_html += '</div>'
                st.markdown(chips_html, unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

        # D. Smart Recommendations
        recs = profile.get('recommendations', [])
        if recs:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#FFC048;"></div>
                <h3>AI Recommendations</h3>
            </div>''', unsafe_allow_html=True)

            for rec in recs[:10]:
                pc = {'High': '#FF7675', 'Medium': '#FFC048', 'Low': '#8E9AA8'}.get(rec.get('priority', 'Low'), '#8E9AA8')
                bc = {'High': 'high', 'Medium': 'medium', 'Low': 'low'}.get(rec.get('priority', 'Low'), 'low')
                st.markdown(f'''
                <div class="glass-card" style="padding:12px 16px; margin-bottom:8px; border-left:3px solid {pc};">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div style="display:flex; align-items:center; gap:10px;">
                            <span style="font-size:1.1rem;">{rec.get('icon', '\U0001f4a1')}</span>
                            <strong style="color:var(--text-primary); font-size:0.88rem;">{rec.get('column', '')}</strong>
                            <span style="color:#00D4C8; font-size:0.82rem; font-weight:500;">{rec.get('action', '')}</span>
                        </div>
                        <span class="badge badge-{bc}">{rec.get('priority', 'Low')}</span>
                    </div>
                    <p style="color:#8E9AA8; font-size:0.78rem; margin:4px 0 0 36px;">{rec.get('reason', '')}</p>
                </div>
                ''', unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)

        # E. Data Preview
        st.markdown('''<div class="section-header">
            <div class="accent-dot" style="background:#5B8DEF;"></div>
            <h3>Data Preview</h3>
        </div>''', unsafe_allow_html=True)
        st.dataframe(st.session_state.df.head(100), use_container_width=True, height=280)

        st.markdown("<hr>", unsafe_allow_html=True)

        # F. Missing Values Heatmap + Issues
        col_heat, col_iss = st.columns([1, 1.1])

        with col_heat:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#F97794;"></div>
                <h3>Missing Values Matrix</h3>
            </div>''', unsafe_allow_html=True)
            sample_sz = min(len(st.session_state.df), 500)
            null_df = st.session_state.df.iloc[:sample_sz].isna().astype(int)
            fig_heat = px.imshow(
                null_df.values.T,
                labels=dict(x="Row", y="Column", color="Missing"),
                x=list(range(sample_sz)), y=null_df.columns,
                color_continuous_scale=[[0, '#0F1219'], [1, '#7C6BF0']]
            )
            fig_heat.update_layout(
                coloraxis_showscale=False, height=300,
                margin=dict(t=6, b=6, l=6, r=6),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='#0F1219',
                font=dict(family='Outfit', color='#8B92A0'),
                xaxis=dict(color='#8E9AA8', showticklabels=False), yaxis=dict(color='#8B92A0')
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        with col_iss:
            st.markdown('''<div class="section-header">
                <div class="accent-dot" style="background:#FF7675;"></div>
                <h3>Detected Issues</h3>
            </div>''', unsafe_allow_html=True)
            issues = profile["issues"]
            if not issues:
                st.markdown('<div class="glass-card" style="text-align:center; padding:24px;"><span style="font-size:1.5rem;">\U0001f389</span><p style="color:#0BE881; font-weight:600; margin-top:8px;">No issues detected!</p></div>', unsafe_allow_html=True)
            else:
                iss_container = st.container(height=300)
                with iss_container:
                    for iss in sorted(issues, key=lambda x: {'High':0,'Medium':1,'Low':2}.get(x['severity'],3)):
                        sev_icon = {
                            'High': '<span style="color:#FF7675;">\u25cf</span>',
                            'Medium': '<span style="color:#FFC048;">\u25cf</span>',
                            'Low': '<span style="color:#8E9AA8;">\u25cf</span>'
                        }.get(iss['severity'], '')
                        bc = {'High':'high','Medium':'medium','Low':'low'}.get(iss['severity'],'low')
                        st.markdown(f'''<div style="padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.04);">
                            {sev_icon} <strong style="color:var(--text-primary); font-size:0.82rem;">[{iss['dimension']}]</strong>
                            <span style="color:#8B92A0; font-size:0.8rem;"> {iss['description']}</span>
                            <span class="badge badge-{bc}" style="margin-left:8px;">{iss['severity']}</span>
                        </div>''', unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        # G. Column Breakdown
        st.markdown('''<div class="section-header">
            <div class="accent-dot" style="background:#B48DF3;"></div>
            <h3>Column-Level Analysis</h3>
        </div>''', unsafe_allow_html=True)

        for col_name, col_info in profile["columns"].items():
            null_indicator = f' \u2022 <span style="color:#FF7675;">{col_info["null_count"]} nulls ({col_info["null_pct"]:.1f}%)</span>' if col_info['null_count'] > 0 else ' \u2022 <span style="color:#0BE881;">No nulls</span>'
            with st.expander(f"\U0001f539 {col_name} \u2014 {col_info['inferred_type']}"):
                cl, cr = st.columns([1, 1])
                with cl:
                    st.markdown(f'''
                    <div class="glass-card" style="padding:14px;">
                        <div style="color:#8E9AA8; font-size:0.7rem; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:8px; font-weight:600;">Column Diagnostics</div>
                        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
                            <div><span style="color:#8E9AA8; font-size:0.75rem;">Type:</span><br><strong style="color:var(--text-primary); font-size:0.85rem;">{col_info['dtype']}</strong></div>
                            <div><span style="color:#8E9AA8; font-size:0.75rem;">Inferred:</span><br><strong style="color:#00D4C8; font-size:0.85rem;">{col_info['inferred_type']}</strong></div>
                            <div><span style="color:#8E9AA8; font-size:0.75rem;">Unique:</span><br><strong style="color:var(--text-primary); font-size:0.85rem;">{col_info['unique_count']}</strong></div>
                            <div><span style="color:#8E9AA8; font-size:0.75rem;">Nulls:</span><br><strong style="color:#F97794; font-size:0.85rem;">{col_info['null_count']} ({col_info['null_pct']:.1f}%)</strong></div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                    if col_info['inferred_type'] == 'Numeric':
                        st.markdown(f'''
                        <div class="glass-card" style="padding:14px; margin-top:8px;">
                            <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px;">
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Mean</span><br><strong style="color:var(--text-primary);">{col_info.get('mean',0):.2f}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Median</span><br><strong style="color:var(--text-primary);">{col_info.get('median',0):.2f}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Std</span><br><strong style="color:var(--text-primary);">{col_info.get('std',0):.2f}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Min</span><br><strong style="color:var(--text-primary);">{col_info.get('min',0):.2f}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Max</span><br><strong style="color:var(--text-primary);">{col_info.get('max',0):.2f}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.7rem;">Outliers</span><br><strong style="color:#FFC048;">{col_info.get('outliers_count',0)}</strong></div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

                with cr:
                    if col_info['inferred_type'] == 'Numeric':
                        col_vals = pd.to_numeric(st.session_state.df[col_name], errors='coerce').dropna()
                        if not col_vals.empty:
                            fig_h = px.histogram(col_vals, nbins=30)
                            fig_h.update_layout(height=200, showlegend=False, **get_dark_plotly_template()['layout'])
                            fig_h.update_traces(marker_color='#7C6BF0', marker_line_width=0)
                            st.plotly_chart(fig_h, use_container_width=True)
                    elif col_info['inferred_type'] in ['Categorical', 'Boolean'] and col_info.get('top_values'):
                        tv = col_info['top_values']
                        fig_b = px.bar(x=list(tv.keys()), y=list(tv.values()), labels={'x':'', 'y':'Count'})
                        fig_b.update_layout(height=200, showlegend=False, **get_dark_plotly_template()['layout'])
                        fig_b.update_traces(marker_color='#00D4C8', marker_line_width=0)
                        st.plotly_chart(fig_b, use_container_width=True)

    # ============================================================
    # TAB 2: AGENT CONSOLE
    # ============================================================
    with tab2:
        if st.session_state.df is None:
            st.info("\U0001f448 Load a dataset to access the Agent Console.")
        else:
            cleaning_mode = st.radio(
                "Restoration Engine:",
                ["Autonomous GenAI (Gemini)", "Heuristic Rules (Offline)"],
                horizontal=True,
                help="GenAI uses Gemini for cognitive code generation. Heuristic uses deterministic algorithms."
            )
            agent_mode = "genai" if "GenAI" in cleaning_mode else "heuristic"

            if agent_mode == "genai" and not st.session_state.api_key_set:
                st.warning("\U0001f511 API Key required for GenAI mode. Set it in the sidebar or switch to Heuristic.")
            else:
                max_steps = st.number_input("Max Steps:", min_value=1, max_value=25, value=12, label_visibility="collapsed")
                col_btn, col_rollback, col_info = st.columns([1.2, 1.2, 2.6])
                with col_btn:
                    run_btn = st.button("\U0001f680 Launch Agent", disabled=st.session_state.agent_running, use_container_width=True)
                with col_rollback:
                    rollback_btn = st.button("↩️ Rollback", disabled=st.session_state.agent_running or not st.session_state.action_log, use_container_width=True)
                with col_info:
                    st.markdown(f'<p style="color:#8E9AA8; font-size:0.78rem; margin-top:8px;">Mode: <strong style="color:#7C6BF0;">{agent_mode.upper()}</strong> \u2022 Max steps: <strong style="color:#00D4C8;">{max_steps}</strong></p>', unsafe_allow_html=True)

                if rollback_btn:
                    with st.spinner("Rolling back last action..."):
                        session_id = st.session_state.session_id
                        history = st.session_state.session_store.get_session_history(session_id)
                        
                        if len(history) > 0:
                            prev_step = len(history) - 1
                            try:
                                prev_df = st.session_state.session_store.load_dataframe_snapshot(session_id, prev_step)
                                
                                # Remove the last step records
                                with st.session_state.session_store._get_connection() as conn:
                                    conn.execute("DELETE FROM action_traces WHERE session_id = ? AND step = ?", (session_id, len(history)))
                                    conn.execute("DELETE FROM profiles WHERE session_id = ? AND step = ?", (session_id, len(history)))
                                    conn.execute("UPDATE sessions SET current_step = ? WHERE session_id = ?", (prev_step, session_id))
                                    conn.commit()
                                    
                                # Remove parquet file
                                prev_filepath = os.path.join(st.session_state.session_store.db_dir, session_id, f"step_{len(history)}.parquet")
                                if os.path.exists(prev_filepath):
                                    os.remove(prev_filepath)
                                    
                                # Restore session state variables
                                st.session_state.df = prev_df.copy()
                                if prev_step == 0:
                                    st.session_state.cleaned_df = None
                                    st.session_state.comparison = None
                                    st.session_state.action_log = []
                                    st.session_state.current_profile = st.session_state.initial_profile
                                else:
                                    st.session_state.cleaned_df = prev_df.copy()
                                    prev_prof = st.session_state.session_store.get_latest_profile(session_id)
                                    st.session_state.current_profile = prev_prof
                                    st.session_state.comparison = compare_profiles(st.session_state.initial_profile, prev_prof)
                                    st.session_state.action_log = st.session_state.session_store.get_session_history(session_id)
                                    
                                st.session_state.console_lines.append(f"[SYSTEM] Rolled back last step. Reverted to step {prev_step}.")
                                st.success(f"Successfully rolled back last step. Reverted to step {prev_step}!")
                                time.sleep(0.8)
                                st.rerun()
                            except Exception as ex:
                                st.error(f"Rollback failed: {str(ex)}")

                # Terminal Chrome
                st.markdown(f'''
                <div style="background:#151921; border-radius:14px 14px 0 0; padding:10px 16px; display:flex; align-items:center; gap:8px; border:1px solid rgba(255,255,255,0.06); border-bottom:none; margin-top:16px;">
                    <div style="width:11px; height:11px; border-radius:50%; background:#FF7675;"></div>
                    <div style="width:11px; height:11px; border-radius:50%; background:#FFC048;"></div>
                    <div style="width:11px; height:11px; border-radius:50%; background:#0BE881;"></div>
                    <span style="color:#8E9AA8; font-family:'JetBrains Mono', monospace; font-size:0.72rem; margin-left:12px;">dataclean-agent \u2014 {agent_mode}</span>
                    <span style="margin-left:auto; color:#8E9AA8; font-family:'JetBrains Mono', monospace; font-size:0.68rem;">\u25cf live</span>
                </div>
                ''', unsafe_allow_html=True)

                console_placeholder = st.empty()

                def render_console():
                    html = "<div class='console-box'>"
                    for line in st.session_state.console_lines:
                        if "[THOUGHT]" in line or "[THINKING]" in line:
                            html += f"<div class='console-line console-thought'>{line}</div>"
                        elif "[CODE]" in line:
                            html += f"<div class='console-line console-code'>{line}</div>"
                        elif "[SUCCESS]" in line:
                            html += f"<div class='console-line console-success'>{line}</div>"
                        elif "[ERROR]" in line or "[HEALING]" in line:
                            html += f"<div class='console-line console-error'>{line}</div>"
                        elif "[SYSTEM]" in line:
                            html += f"<div class='console-line console-system'>{line}</div>"
                        else:
                            html += f"<div class='console-line'>{line}</div>"
                    html += "<span class='console-cursor'></span>"
                    html += "</div>"
                    console_placeholder.markdown(html, unsafe_allow_html=True)

                render_console()

                # Stats bar
                stats_placeholder = st.empty()
                if st.session_state.cleaned_df is not None and not st.session_state.agent_running:
                    sd = len(st.session_state.action_log)
                    sf = len([a for a in st.session_state.action_log if a.get('error')])
                    stats_placeholder.markdown(f'''
                    <div style="display:flex; gap:1px; background:rgba(255,255,255,0.04); border-radius:0 0 14px 14px; overflow:hidden; border:1px solid rgba(255,255,255,0.06); border-top:none;">
                        <div style="flex:1; padding:12px 16px; background:#151921;">
                            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Steps</div>
                            <div style="color:#7C6BF0; font-size:1.1rem; font-weight:700;">{sd}</div>
                        </div>
                        <div style="flex:1; padding:12px 16px; background:#151921;">
                            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Success</div>
                            <div style="color:#0BE881; font-size:1.1rem; font-weight:700;">{sd - sf}</div>
                        </div>
                        <div style="flex:1; padding:12px 16px; background:#151921;">
                            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Failed</div>
                            <div style="color:#FF7675; font-size:1.1rem; font-weight:700;">{sf}</div>
                        </div>
                        <div style="flex:1; padding:12px 16px; background:#151921;">
                            <div style="color:#8E9AA8; font-size:0.65rem; text-transform:uppercase; letter-spacing:0.08em;">Status</div>
                            <div style="color:#0BE881; font-size:1.1rem; font-weight:700;">Done</div>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

                # Agent Execution Loop (PRESERVED EXACTLY)
                if run_btn:
                    st.session_state.agent_running = True
                    st.session_state.console_lines = [f"[SYSTEM] Initializing {agent_mode.upper()} engine..."]
                    render_console()

                    agent = CleaningAgent(st.session_state.raw_df, st.session_state.initial_profile, mode=agent_mode)
                    progress_bar = st.progress(0.0)

                    completed = False
                    for step_idx in range(max_steps):
                        progress_val = float(step_idx + 1) / max_steps
                        progress_bar.progress(progress_val)

                        try:
                            step_agent = CleaningAgent(
                                agent.df,
                                st.session_state.initial_profile if step_idx == 0 else profile_dataset(agent.df),
                                mode=agent_mode
                            )
                            step_agent.chat_history = agent.chat_history
                            step_agent.action_log = agent.action_log
                            step_agent.step_count = agent.step_count

                            step_gen = step_agent.run_cleaning_step()

                            for update in step_gen:
                                status = update["status"]
                                msg = update["message"]

                                if status == "thinking":
                                    st.session_state.console_lines.append(f"[THINKING] Step {update['step']}: {msg}")
                                elif status == "executing":
                                    st.session_state.console_lines.append(f"[THOUGHT] {update['thought']}")
                                    st.session_state.console_lines.append(f"[CODE] {update['code']}")
                                elif status == "healing":
                                    st.session_state.console_lines.append(f"[HEALING] Attempt {update['attempt']} failed: {update['error']}")
                                    st.session_state.console_lines.append(f"[HEALING] {msg}")
                                elif status == "success":
                                    # --- VALIDATION LAYER ---
                                    verifier = TransformationVerifier()
                                    val_res = verifier.verify(step_agent.df, update["df"])
                                    
                                    # Output validation warnings if any
                                    for warning in val_res.warnings:
                                        st.session_state.console_lines.append(f"[VALIDATION] {warning}")
                                        
                                    if not val_res.passed:
                                        crit_msg = val_res.warnings[0] if val_res.warnings else "Critical check failed."
                                        st.session_state.console_lines.append(f"[VALIDATION FAILED] Reverting step: {crit_msg}")
                                        completed = True
                                        break
                                        
                                    st.session_state.console_lines.append(f"[SUCCESS] {msg}")
                                    agent.df = update["df"]
                                    agent.action_log = step_agent.action_log
                                    agent.chat_history = step_agent.chat_history
                                    agent.step_count = step_agent.step_count
                                    
                                    # --- PERSISTENCE LAYER ---
                                    session_id = st.session_state.session_id
                                    step_num = agent.step_count
                                    last_action = agent.action_log[-1]
                                    
                                    st.session_state.session_store.save_action(
                                        session_id=session_id,
                                        step=step_num,
                                        action_name=last_action.get("action_name", "unknown_action"),
                                        action_args=last_action.get("action_args", {}),
                                        justification=last_action.get("justification", ""),
                                        code=last_action.get("code", "")
                                    )
                                    
                                    # Profile the new state
                                    current_prof = profile_dataset(agent.df)
                                    st.session_state.session_store.save_profile(session_id, step_num, current_prof)
                                    st.session_state.session_store.save_dataframe_snapshot(session_id, step_num, agent.df)
                                elif status == "failed":
                                    st.session_state.console_lines.append(f"[ERROR] Step {update['step']} failed: {msg}")
                                    agent.action_log = step_agent.action_log
                                    agent.chat_history = step_agent.chat_history
                                    agent.step_count = step_agent.step_count
                                elif status == "completed":
                                    st.session_state.console_lines.append(f"[SYSTEM] {msg}")
                                    completed = True
                                    break
                                elif status == "api_error":
                                    st.session_state.console_lines.append(f"[ERROR] {msg}")
                                    completed = True
                                    break

                                render_console()

                            if completed:
                                break

                        except Exception as ex:
                            st.session_state.console_lines.append(f"[ERROR] Exception: {str(ex)}")
                            render_console()
                            break

                    st.session_state.df = agent.df.copy()
                    st.session_state.cleaned_df = agent.df.copy()
                    st.session_state.action_log = agent.action_log

                    with st.spinner("Analyzing cleaned dataset..."):
                        final_profile = profile_dataset(st.session_state.df)
                        st.session_state.current_profile = final_profile
                        st.session_state.comparison = compare_profiles(st.session_state.initial_profile, final_profile)

                    st.session_state.console_lines.append(f"[SYSTEM] Pipeline complete \u2014 Final Score: {final_profile['overall_score']:.1f}%")
                    render_console()
                    progress_bar.progress(1.0)
                    st.session_state.agent_running = False

                    st.success("\U0001f389 Cleaning complete! Check the Compare tab.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()

    # ============================================================
    # TAB 3: COMPARE
    # ============================================================
    with tab3:
        if st.session_state.cleaned_df is None:
            st.info("\U0001f4a1 Run the Agent Console first to generate comparison data.")
        else:
            comp = st.session_state.comparison

            # A. Hero Delta Cards
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                bc = score_color(comp['overall_before'])
                st.markdown(f'''
                <div class="glass-card" style="text-align:center; padding:20px 12px; border-top:2px solid {bc};">
                    <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Before</div>
                    <div style="color:{bc}; font-size:2.2rem; font-weight:800; font-family:'Outfit'; line-height:1.2; margin-top:4px;">{comp['overall_before']:.1f}%</div>
                </div>''', unsafe_allow_html=True)
            with c2:
                ac = score_color(comp['overall_after'])
                st.markdown(f'''
                <div class="glass-card" style="text-align:center; padding:20px 12px; border-top:2px solid {ac};">
                    <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">After</div>
                    <div style="color:{ac}; font-size:2.2rem; font-weight:800; font-family:'Outfit'; line-height:1.2; margin-top:4px;">{comp['overall_after']:.1f}%</div>
                </div>''', unsafe_allow_html=True)
            with c3:
                delta = comp['overall_delta']
                dc = '#0BE881' if delta >= 0 else '#FF7675'
                sign = '+' if delta >= 0 else ''
                st.markdown(f'''
                <div class="glass-card" style="text-align:center; padding:20px 12px; border-top:2px solid {dc};">
                    <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Improvement</div>
                    <div style="color:{dc}; font-size:2.2rem; font-weight:800; font-family:'Outfit'; line-height:1.2; margin-top:4px;">{sign}{delta:.1f}%</div>
                </div>''', unsafe_allow_html=True)
            with c4:
                nr = comp['summary_before']['total_nulls'] - comp['summary_after']['total_nulls']
                st.markdown(f'''
                <div class="glass-card" style="text-align:center; padding:20px 12px; border-top:2px solid #F97794;">
                    <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;">Nulls Fixed</div>
                    <div style="color:#F97794; font-size:2.2rem; font-weight:800; font-family:'Outfit'; line-height:1.2; margin-top:4px;">{nr:,}</div>
                </div>''', unsafe_allow_html=True)
            st.markdown("<hr>", unsafe_allow_html=True)

            # A.2 Health Score Gauge
            st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#8B5CF6;"></div><h3>Unified Data Health Score</h3></div>''', unsafe_allow_html=True)
            
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = comp['overall_after'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                delta = {'reference': comp['overall_before'], 'increasing': {'color': "#0BE881"}, 'decreasing': {'color': "#FF7675"}},
                gauge = {
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#8E9AA8", 'tickfont': {'color': '#8E9AA8'}},
                    'bar': {'color': score_color(comp['overall_after'])},
                    'bgcolor': "rgba(0,0,0,0)",
                    'borderwidth': 1,
                    'bordercolor': "#2d3340",
                    'steps': [
                        {'range': [0, 50], 'color': 'rgba(255, 118, 117, 0.05)'},
                        {'range': [50, 80], 'color': 'rgba(253, 203, 110, 0.05)'},
                        {'range': [80, 100], 'color': 'rgba(11, 232, 129, 0.05)'}],
                    'threshold': {
                        'line': {'color': "#f8fafc", 'width': 4},
                        'thickness': 0.75,
                        'value': comp['overall_after']}
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=30,b=20,l=40,r=40), paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Space Grotesk', color='#C8CDD5', size=18))
            st.plotly_chart(fig_gauge, use_container_width=True)

            st.markdown("<hr>", unsafe_allow_html=True)
            # B. Dual Radar + Bar
            cr1, cr2 = st.columns(2)
            with cr1:
                st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#7C6BF0;"></div><h3>Quality Radar Overlay</h3></div>''', unsafe_allow_html=True)
                cats = list(comp['dimensions'].keys())
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=[comp['dimensions'][c]['before'] for c in cats] + [comp['dimensions'][cats[0]]['before']],
                    theta=cats + [cats[0]], fill='toself', name='Before',
                    line=dict(color='#FF7675', width=2), fillcolor='rgba(255,118,117,0.1)',
                    marker=dict(size=5)
                ))
                fig_r.add_trace(go.Scatterpolar(
                    r=[comp['dimensions'][c]['after'] for c in cats] + [comp['dimensions'][cats[0]]['after']],
                    theta=cats + [cats[0]], fill='toself', name='After',
                    line=dict(color='#0BE881', width=2), fillcolor='rgba(11,232,129,0.1)',
                    marker=dict(size=5)
                ))
                fig_r.update_layout(
                    polar=dict(bgcolor='rgba(0,0,0,0)',
                        radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=8, color='#8E9AA8'), gridcolor='rgba(255,255,255,0.04)'),
                        angularaxis=dict(tickfont=dict(size=10, color='#C8CDD5'), gridcolor='rgba(255,255,255,0.06)')
                    ),
                    showlegend=True, height=360, margin=dict(t=30,b=20,l=45,r=45),
                    paper_bgcolor='rgba(0,0,0,0)', font=dict(family='Outfit', color='#C8CDD5'),
                    legend=dict(orientation="h", y=1.08, x=0.5, xanchor='center', font=dict(color='#C8CDD5', size=11))
                )
                st.plotly_chart(fig_r, use_container_width=True)

            with cr2:
                st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#00D4C8;"></div><h3>Dimension Comparison</h3></div>''', unsafe_allow_html=True)
                fig_b = go.Figure()
                fig_b.add_trace(go.Bar(x=cats, y=[comp['dimensions'][c]['before'] for c in cats], name='Before', marker_color='#FF7675', marker_cornerradius=4))
                fig_b.add_trace(go.Bar(x=cats, y=[comp['dimensions'][c]['after'] for c in cats], name='After', marker_color='#0BE881', marker_cornerradius=4))
                fig_b.update_layout(
                    barmode='group', height=360, **get_dark_plotly_template()['layout'],
                    legend=dict(orientation="h", y=1.08, x=0.5, xanchor='center', font=dict(color='#C8CDD5', size=11)),
                    yaxis_title='Score (%)'
                )
                st.plotly_chart(fig_b, use_container_width=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            # C. Column Restorations
            st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#F97794;"></div><h3>Column Restorations</h3></div>''', unsafe_allow_html=True)
            col_list = []
            for cn, d in comp["columns"].items():
                col_list.append({
                    "Column": cn, "Type": d["type_after"],
                    "Nulls Before": d["null_count_before"], "Nulls After": d["null_count_after"],
                    "Outliers Before": d.get("outliers_before", "-"), "Outliers After": d.get("outliers_after", "-")
                })
            st.dataframe(pd.DataFrame(col_list), hide_index=True, use_container_width=True, height=250)

            st.markdown("<hr>", unsafe_allow_html=True)

            # D. Cleaning Timeline
            if st.session_state.action_log:
                st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#B48DF3;"></div><h3>Cleaning Timeline</h3></div>''', unsafe_allow_html=True)
                for i, action in enumerate(st.session_state.action_log):
                    ac = dim_color(list(dims.keys())[i % 6]) if i < 20 else '#7C6BF0'
                    is_err = bool(action.get('error'))
                    status_badge = '<span class="badge badge-high">Failed</span>' if is_err else '<span class="badge badge-success">Success</span>'
                    st.markdown(f'''
                    <div style="display:flex; align-items:flex-start; gap:14px; margin-bottom:10px;">
                        <div style="min-width:34px; height:34px; border-radius:50%; background:{ac}15; border:2px solid {ac};
                            display:flex; align-items:center; justify-content:center; color:{ac}; font-weight:700; font-size:0.8rem; flex-shrink:0;">{i+1}</div>
                        <div class="glass-card" style="flex:1; padding:12px 16px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <strong style="color:var(--text-primary); font-size:0.85rem;">{action.get('justification', 'Cleaning step')}</strong>
                                {status_badge}
                            </div>
                            <p style="color:#8E9AA8; font-size:0.75rem; margin:4px 0 0 0;">Shape: {action.get('shape_after', 'N/A')}</p>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            # E. Distribution Overlay
            st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#FFC048;"></div><h3>Distribution Comparison</h3></div>''', unsafe_allow_html=True)
            numeric_cols = [c for c, t in st.session_state.initial_profile["columns"].items() if t["inferred_type"] == "Numeric"]
            if numeric_cols:
                sel_col = st.selectbox("Numeric Column:", numeric_cols, label_visibility="collapsed")
                fig_d = go.Figure()
                raw_v = pd.to_numeric(st.session_state.raw_df[sel_col], errors='coerce').dropna()
                fig_d.add_trace(go.Histogram(x=raw_v, name='Before', marker_color='rgba(255,118,117,0.5)', nbinsx=40))
                clean_v = pd.to_numeric(st.session_state.cleaned_df[sel_col], errors='coerce').dropna()
                fig_d.add_trace(go.Histogram(x=clean_v, name='After', marker_color='rgba(11,232,129,0.5)', nbinsx=40))
                fig_d.update_layout(
                    barmode='overlay', height=280, **get_dark_plotly_template()['layout'],
                    legend=dict(orientation="h", y=1.08, x=0.5, xanchor='center', font=dict(color='#C8CDD5'))
                )
                fig_d.update_traces(opacity=0.6)
                st.plotly_chart(fig_d, use_container_width=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            csv_data = st.session_state.cleaned_df.to_csv(index=False)
            st.download_button("\U0001f4be Download Cleaned Dataset (CSV)", data=csv_data, file_name="cleaned_dataset.csv", mime="text/csv", use_container_width=True)

    # ============================================================
    # TAB 4: REPORT & AUDIT
    # ============================================================
    with tab4:
        if st.session_state.cleaned_df is None:
            st.info("\U0001f4a1 Run the Agent Console first to generate the audit report.")
        else:
            st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#7C6BF0;"></div><h3>Cleaning Audit Trail</h3></div>''', unsafe_allow_html=True)

            if st.session_state.action_log:
                for i, action in enumerate(st.session_state.action_log):
                    sc = '#7C6BF0' if i % 2 == 0 else '#00D4C8'
                    is_err = bool(action.get('error'))
                    step_label = f"Step {action.get('step', i+1)}"
                    just = action.get('justification', 'Cleaning step')
                    with st.expander(f"{step_label}: {just[:90]}"):
                        st.markdown(f'''
                        <div class="glass-card" style="border-left:3px solid {sc};">
                            <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; font-weight:600;">Justification</div>
                            <p style="color:var(--text-primary); font-size:0.88rem; margin-bottom:14px;">{just}</p>
                            <div style="color:#8E9AA8; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; font-weight:600;">Generated Code</div>
                            <div class="console-box" style="min-height:auto; max-height:200px; border-radius:8px; font-size:0.78rem;">
                                <code style="color:#FFC048; font-family:'JetBrains Mono'; white-space:pre-wrap;">{action.get('code', 'N/A')}</code>
                            </div>
                            <div style="display:flex; gap:16px; margin-top:12px;">
                                <div><span style="color:#8E9AA8; font-size:0.72rem;">Shape:</span> <strong style="color:#0BE881;">{action.get('shape_after', 'N/A')}</strong></div>
                                <div><span style="color:#8E9AA8; font-size:0.72rem;">Status:</span> <strong style="color:{'#FF7675' if is_err else '#0BE881'};">{'Failed' if is_err else 'Success'}</strong></div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)

            st.markdown("<hr>", unsafe_allow_html=True)

            # Export Panel
            st.markdown('''<div class="section-header"><div class="accent-dot" style="background:#00D4C8;"></div><h3>Export Reports</h3></div>''', unsafe_allow_html=True)

            comp = st.session_state.comparison
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                metadata = {
                    'overall_before': comp['overall_before'],
                    'overall_after': comp['overall_after'],
                    'overall_delta': comp['overall_delta'],
                    'dimensions': comp['dimensions'],
                    'action_count': len(st.session_state.action_log),
                    'actions': st.session_state.action_log
                }
                json_data = json.dumps(metadata, indent=2, default=str)
                st.download_button('\U0001f4e6 JSON Metadata', data=json_data, file_name='cleaning_metadata.json', mime='application/json', use_container_width=True)

            with ce2:
                if st.button("\U0001f4c4 Gen DOCX Report", type="primary", use_container_width=True):
                    with st.spinner("Compiling report..."):
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
                                report_path = tmp.name
                            generate_docx_report(
                                comparison=st.session_state.comparison,
                                action_log=st.session_state.action_log,
                                initial_issues=st.session_state.initial_profile["issues"],
                                output_path=report_path
                            )
                            with open(report_path, "rb") as f:
                                docx_bytes = f.read()
                            os.unlink(report_path)
                            st.session_state.docx_bytes = docx_bytes
                            st.success("\u2705 DOCX Generated!")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                            st.code(traceback.format_exc())

            with ce3:
                script_lines = [
                    "import pandas as pd", 
                    "import numpy as np", 
                    "", 
                    "def clean_data(df: pd.DataFrame) -> pd.DataFrame:",
                    "    df = df.copy()"
                ]
                for action in st.session_state.action_log:
                    try:
                        code_snippet = get_action_python_code(action['action_name'], **action.get('action_args', {}))
                        script_lines.append(f"    # Step {action.get('step', '?')}: {action.get('action_name')}")
                        for line in code_snippet.strip().split('\\n'):
                            script_lines.append("    " + line)
                    except Exception:
                        script_lines.append("    # Error generating code for " + action.get('action_name', 'unknown'))
                
                script_lines.append("    return df")
                script_lines.append("")
                script_lines.append("if __name__ == '__main__':")
                script_lines.append("    # df = pd.read_csv('raw_data.csv')")
                script_lines.append("    # cleaned_df = clean_data(df)")
                script_lines.append("    # cleaned_df.to_csv('cleaned_data.csv', index=False)")
                
                py_script = "\n".join(script_lines)
                st.download_button('🐍 Python Script', data=py_script, file_name='cleaning_script.py', mime='text/plain', use_container_width=True)

            if 'docx_bytes' in st.session_state:
                st.download_button(
                    "\U0001f4e5 Download DOCX Report",
                    data=st.session_state.docx_bytes,
                    file_name="data_quality_audit_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
