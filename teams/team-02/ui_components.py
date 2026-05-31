import re
from typing import List
from essay_analyzer import FlaggedPhrase

# Pure Premium CSS for the "Midnight Glow" Glassmorphism Theme
GLASS_CSS = """
<style>
/* Import modern Outfit font */
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

/* Force luxurious dark mode background app-wide with maximum specificity */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main {
    background: radial-gradient(circle at 50% 50%, #151130 0%, #0c0919 100%) !important;
    background-color: #0c0919 !important;
    color: #e2e8f0 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Tab styling premium styling */
[data-testid="stTabBar"] {
    background: rgba(255, 255, 255, 0.02) !important;
    border-radius: 12px !important;
    padding: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.05) !important;
}
[data-testid="stTab"] {
    font-weight: 500 !important;
    color: #94a3b8 !important;
    border-radius: 8px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stTab"]:hover {
    color: #c084fc !important;
    background: rgba(255, 255, 255, 0.03) !important;
}
[data-testid="stTab"][aria-selected="true"] {
    color: #ffffff !important;
    background: linear-gradient(135deg, rgba(147, 51, 234, 0.2), rgba(99, 102, 241, 0.2)) !important;
    border: 1px solid rgba(168, 85, 247, 0.4) !important;
}

/* Hide Streamlit default elements but keep the sidebar toggle button fully functional */
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
/* Keep the header structure intact so that the expand toggle (>) is always visible,
   but hide the deploy button and the colored top decoration bar. */
[data-testid="stHeaderActionElements"] {display: none !important;}
[data-testid="stHeader"] {background: transparent !important;}

/* Force the sidebar expand/collapse toggle buttons (>) to be extremely visible, glowing, and premium */
[data-testid="stSidebarCollapse"] button, 
[data-testid="collapsedControl"] button, 
button[data-testid="collapsedControl"],
.stSidebarCollapse button {
    background-color: rgba(139, 92, 246, 0.15) !important;
    border: 1px solid rgba(139, 92, 246, 0.45) !important;
    color: #c084fc !important;
    border-radius: 8px !important;
    box-shadow: 0 0 12px rgba(139, 92, 246, 0.3) !important;
    transition: all 0.3s ease !important;
    visibility: visible !important;
    display: flex !important;
}

[data-testid="stSidebarCollapse"] button:hover, 
[data-testid="collapsedControl"] button:hover, 
button[data-testid="collapsedControl"]:hover,
.stSidebarCollapse button:hover {
    background-color: rgba(139, 92, 246, 0.35) !important;
    border: 1px solid rgba(168, 85, 247, 0.75) !important;
    color: #ffffff !important;
    box-shadow: 0 0 18px rgba(168, 85, 247, 0.5) !important;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}
::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.02);
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.2);
}

/* Glassmorphism General Card Styling */
.glass-card {
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 26px;
    margin-bottom: 22px;
    box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
    transition: all 0.3s ease;
}
.glass-card:hover {
    border: 1px solid rgba(168, 85, 247, 0.25);
    box-shadow: 0 16px 48px 0 rgba(147, 51, 234, 0.18);
}

/* Score Card Header Badge */
.score-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 9999px;
    font-weight: 700;
    font-size: 1.1rem;
    text-align: center;
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.1);
}
.score-high {
    background: linear-gradient(135deg, #10b981, #059669);
    color: #ffffff;
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}
.score-medium {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    color: #ffffff;
    box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}
.score-low {
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #ffffff;
    box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

/* Main Dashboard Title with sleek neon gradient */
.app-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #c084fc 0%, #6366f1 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 5px;
    text-align: left;
    filter: drop-shadow(0 2px 8px rgba(99, 102, 241, 0.3));
}
.app-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    margin-bottom: 30px;
    font-weight: 300;
}

/* Section Titles */
.section-title {
    font-size: 1.6rem;
    font-weight: 600;
    margin-top: 10px;
    margin-bottom: 20px;
    color: #f1f5f9;
    border-left: 4px solid #c084fc;
    padding-left: 12px;
}

/* Highlighted Essay Document Canvas (Luxurious Virtual Paper Layout) */
.essay-viewer {
    background: rgba(15, 12, 30, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-left: 6px solid #8b5cf6;
    border-radius: 16px;
    padding: 30px;
    font-size: 1.15rem;
    line-height: 1.9;
    color: #cbd5e1;
    white-space: pre-wrap; /* maintain linebreaks */
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 10px 30px rgba(0, 0, 0, 0.5);
    position: relative;
}

/* Interactive Plagiarism/Unoriginality Highlighter (Hover Tooltips) */
.flagged-phrase {
    position: relative;
    background-color: rgba(245, 158, 11, 0.16);
    border-bottom: 2px dashed #f59e0b;
    cursor: pointer;
    transition: all 0.2s ease;
    padding: 2px 0;
    border-radius: 3px;
    font-weight: 450;
}
.flagged-phrase:hover {
    background-color: rgba(245, 158, 11, 0.32);
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.35);
    color: #ffffff;
}

/* Tooltip Styling */
.flagged-phrase .phrase-tooltip {
    visibility: hidden;
    width: 340px;
    background-color: #090614;
    color: #e2e8f0;
    text-align: left;
    border-radius: 14px;
    padding: 18px;
    position: absolute;
    z-index: 1000;
    bottom: 125%; /* Position above the phrase */
    left: 50%;
    transform: translateX(-50%);
    opacity: 0;
    transition: opacity 0.3s, transform 0.3s;
    border: 1px solid rgba(245, 158, 11, 0.5);
    box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.85);
    font-size: 0.9rem;
    line-height: 1.5;
    white-space: normal;
}
.flagged-phrase:hover .phrase-tooltip {
    visibility: visible;
    opacity: 1;
    transform: translate(-50%, -6px);
}
.phrase-tooltip::after {
    content: "";
    position: absolute;
    top: 100%; /* At the bottom of the tooltip */
    left: 50%;
    margin-left: -8px;
    border-width: 8px;
    border-style: solid;
    border-color: #090614 transparent transparent transparent;
}
.tooltip-header {
    font-weight: 700;
    color: #f59e0b;
    margin-bottom: 8px;
    font-size: 0.95rem;
    display: flex;
    align-items: center;
}
.tooltip-reason {
    color: #94a3b8;
    margin-bottom: 12px;
    font-size: 0.85rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 8px;
}
.tooltip-suggestions {
    margin: 0;
    padding-left: 15px;
}
.tooltip-suggestions li {
    margin-bottom: 6px;
    color: #10b981;
    font-weight: 500;
}
.tooltip-suggestions li::marker {
    color: #a855f7;
}

/* Beautiful Inline Diff Comparison Styling */
.diff-viewer {
    background: rgba(15, 12, 30, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-left: 6px solid #10b981;
    border-radius: 16px;
    padding: 30px;
    font-size: 1.15rem;
    line-height: 1.9;
    color: #cbd5e1;
    box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.8), 0 10px 30px rgba(0, 0, 0, 0.5);
}
.diff-del {
    background-color: rgba(239, 68, 68, 0.22);
    color: #fca5a5;
    text-decoration: line-through;
    padding: 2px 5px;
    border-radius: 4px;
    border: 1px solid rgba(239, 68, 68, 0.3);
}
.diff-ins {
    background-color: rgba(16, 185, 129, 0.22);
    color: #a7f3d0;
    padding: 2px 5px;
    border-radius: 4px;
    border: 1px solid rgba(16, 185, 129, 0.3);
    font-weight: 500;
}

/* Sidebar Custom Look */
[data-testid="stSidebar"] {
    background-color: #07050f !important;
    border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
}

/* Canvas Mode Header Floating Badge */
.canvas-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}
.canvas-badge {
    background: rgba(139, 92, 246, 0.15);
    border: 1px solid rgba(139, 92, 246, 0.35);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #c084fc;
    letter-spacing: 0.05em;
    display: flex;
    align-items: center;
    gap: 6px;
}
.pulse-dot {
    width: 6px;
    height: 6px;
    background-color: #c084fc;
    border-radius: 50%;
    animation: pulse 1.8s infinite;
}
@keyframes pulse {
    0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(192, 132, 252, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(192, 132, 252, 0); }
    100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(192, 132, 252, 0); }
}
</style>
"""

def get_score_class(score: int) -> str:
    """Helper to classify score styling class."""
    if score >= 80:
        return "score-high"
    elif score >= 50:
        return "score-medium"
    else:
        return "score-low"

def render_score_card(title: str, score: int, description: str) -> str:
    """
    Renders a premium glassmorphic scorecard for single criteria.
    """
    score_cls = get_score_class(score)
    return f"""
    <div class="glass-card" style="text-align: center;">
        <div style="font-size: 1.2rem; font-weight: 600; color: #94a3b8; margin-bottom: 12px;">{title}</div>
        <div class="score-badge {score_cls}" style="font-size: 2.2rem; padding: 12px 28px; border-radius: 16px; margin-bottom: 14px;">
            {score}<span style="font-size: 1.2rem; font-weight: 400; opacity: 0.85;">/100</span>
        </div>
        <div style="font-size: 0.9rem; color: #e2e8f0; line-height: 1.5; font-weight: 300;">{description}</div>
    </div>
    """

def build_highlighted_essay_html(essay_text: str, flagged_phrases: List[FlaggedPhrase]) -> str:
    """
    Safely injects CSS interactive tooltip highlights into the essay body.
    Supports robust, whitespace-flexible and case-insensitive regex matching.
    """
    if not essay_text:
        return ""

    escaped_text = (
        essay_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    badge_html = """
    <div class="canvas-header">
        <span style="color: #94a3b8; font-size: 0.85rem;">📝 STUDENT ESSAY WORKSPACE</span>
        <span class="canvas-badge"><span class="pulse-dot"></span>ACTIVE COACHING MODE</span>
    </div>
    """

    if not flagged_phrases:
        return f'{badge_html}<div class="essay-viewer">{escaped_text}</div>'

    # Sort flagged phrases by length (descending) to match larger phrases before their substrings
    sorted_phrases = sorted(flagged_phrases, key=lambda x: len(x.phrase), reverse=True)

    # We will build a list of placeholders to prevent nested replacing
    replacements = []
    processed_text = escaped_text

    for idx, fp in enumerate(sorted_phrases):
        orig_phrase = fp.phrase.strip()
        if not orig_phrase:
            continue

        # Escape the original phrase to safely match in the HTML-escaped text
        escaped_phrase = (
            orig_phrase.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        # Build spacing-flexible and case-insensitive regex search pattern
        escaped_regex = re.escape(escaped_phrase)
        # Collapse multiple spaces and newlines into flexible regex spaces (\s+)
        regex_pattern = re.sub(r'\\s+', r'\\s+', escaped_regex)

        try:
            # Check case-insensitively and capture the exact match from the essay text
            match = re.search(f"({regex_pattern})", processed_text, re.IGNORECASE)
            if not match:
                continue
            matched_text = match.group(1)
        except Exception:
            continue

        # Prepare suggestions list HTML
        sug_li = "".join([f"<li>{sug}</li>" for sug in fp.suggestions[:3]])

        # Custom Interactive Highlight Container with the actual matching student text
        highlight_html = (
            f'<span class="flagged-phrase">'
            f'{matched_text}'
            f'<span class="phrase-tooltip">'
            f'  <span class="tooltip-header">⚠️ Originality Warning</span>'
            f'  <div class="tooltip-reason">{fp.reason}</div>'
            f'  <strong style="color: #10b981; font-size: 0.85rem;">Paraphrase Coach:</strong>'
            f'  <ul class="tooltip-suggestions">{sug_li}</ul>'
            f'</span>'
            f'</span>'
        )

        placeholder = f"___FLAGGED_PLACEHOLDER_{idx}___"
        replacements.append((placeholder, highlight_html))
        
        # Replace case-insensitively using regex
        try:
            processed_text = re.sub(f"({regex_pattern})", placeholder, processed_text, flags=re.IGNORECASE, count=1)
        except Exception:
            continue

    # Finally, swap placeholders with the rich HTML highlight blocks
    for placeholder, html in replacements:
        processed_text = processed_text.replace(placeholder, html)

    # Convert newlines to HTML breaks for formatting
    processed_text = processed_text.replace("\n", "<br>")

    return f'{badge_html}<div class="essay-viewer">{processed_text}</div>'

