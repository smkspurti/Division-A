import fitz  # PyMuPDF
import sys
import os

def create_report_pdf():
    # 1. Initialize Document
    doc = fitz.open()
    
    # Page size A4: 595.27 x 841.89 points
    page_width = 595.27
    page_height = 841.89
    
    margin = 54.0  # 0.75 inch
    max_w = page_width - (2 * margin)
    
    current_page = None
    y = 0.0
    
    def start_new_page(title_page=False):
        nonlocal current_page, y
        current_page = doc.new_page(width=page_width, height=page_height)
        y = margin
        
        if not title_page:
            # Draw Header line and text
            current_page.insert_text(
                fitz.Point(margin, 35),
                "DataCleanAgent | Hackathon Technical Report",
                fontsize=8,
                fontname="helv",
                color=(0.36, 0.42, 0.50)
            )
            current_page.draw_line(
                fitz.Point(margin, 42),
                fitz.Point(page_width - margin, 42),
                color=(0.85, 0.87, 0.90),
                width=0.75
            )
            
            # Draw Footer line and text placeholder
            current_page.draw_line(
                fitz.Point(margin, page_height - 42),
                fitz.Point(page_width - margin, page_height - 42),
                color=(0.85, 0.87, 0.90),
                width=0.75
            )
            # Page number is drawn at the end of compilation

    def check_space(needed_h):
        nonlocal y
        if y + needed_h > page_height - margin - 30:
            start_new_page()
            
    def wrap_and_draw_text(text, fontname="helv", fontsize=10, leading=14, color=(0.20, 0.23, 0.27), align=0, style="normal", bullet=False):
        nonlocal y
        
        # Select font variant
        if style == "bold":
            font_variant = "hebo"
        elif style == "italic":
            font_variant = "heit"
        else:
            font_variant = "helv"
            
        indent = 15.0 if bullet else 0.0
        draw_w = max_w - indent
        
        words = text.split(" ")
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            w = fitz.get_text_length(test_line, fontname=font_variant, fontsize=fontsize)
            if w <= draw_w:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
            
        needed_h = len(lines) * leading
        check_space(needed_h)
        
        for idx, line in enumerate(lines):
            px = margin + indent
            if align == 2:  # Right align (simple approximation)
                w = fitz.get_text_length(line, fontname=font_variant, fontsize=fontsize)
                px = page_width - margin - w
            elif align == 1:  # Center align
                w = fitz.get_text_length(line, fontname=font_variant, fontsize=fontsize)
                px = margin + indent + (draw_w - w) / 2.0
                
            # Draw bullet point marker
            if bullet and idx == 0:
                current_page.insert_text(
                    fitz.Point(margin, y + fontsize),
                    "•",
                    fontsize=fontsize + 2,
                    fontname="hebo",
                    color=(0.54, 0.36, 0.96)  # purple accent
                )
                
            current_page.insert_text(
                fitz.Point(px, y + fontsize),
                line,
                fontsize=fontsize,
                fontname=font_variant,
                color=color
            )
            y += leading
        y += 4.0  # paragraph spacing

    # Title Page
    start_new_page(title_page=True)
    
    # Draw Background graphic block
    current_page.draw_rect(
        fitz.Rect(0, 0, page_width, 240),
        color=(0.06, 0.09, 0.16),
        fill=(0.06, 0.09, 0.16)
    )
    # Accent color line
    current_page.draw_line(
        fitz.Point(0, 240),
        fitz.Point(page_width, 240),
        color=(0.54, 0.36, 0.96),
        width=4.0
    )
    
    y = 60.0
    wrap_and_draw_text(
        "DATACLEANAGENT",
        fontname="helv",
        fontsize=28,
        leading=32,
        color=(1.0, 1.0, 1.0),
        style="bold"
    )
    wrap_and_draw_text(
        "Autonomous AI-Powered Data Restoration & Audit Engine",
        fontname="helv",
        fontsize=14,
        leading=18,
        color=(0.85, 0.87, 0.90),
        style="normal"
    )
    
    y = 260.0
    wrap_and_draw_text(
        "HACKATHON TECHNICAL REPORT",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.54, 0.36, 0.96),
        style="bold"
    )
    
    wrap_and_draw_text(
        "Author: Rohi-21",
        fontname="helv",
        fontsize=10,
        leading=14,
        color=(0.36, 0.42, 0.50),
        style="normal"
    )
    wrap_and_draw_text(
        "Date: May 2026",
        fontname="helv",
        fontsize=10,
        leading=14,
        color=(0.36, 0.42, 0.50),
        style="normal"
    )
    wrap_and_draw_text(
        "Version: 1.0 (Production)",
        fontname="helv",
        fontsize=10,
        leading=14,
        color=(0.36, 0.42, 0.50),
        style="normal"
    )
    
    y += 20.0
    
    # Draw Left Border Accent Box for Executive Summary
    check_space(110)
    current_page.draw_rect(
        fitz.Rect(margin, y, page_width - margin, y + 105),
        color=(0.95, 0.96, 0.98),
        fill=(0.95, 0.96, 0.98)
    )
    current_page.draw_line(
        fitz.Point(margin, y),
        fitz.Point(margin, y + 105),
        color=(0.54, 0.36, 0.96),
        width=3.0
    )
    
    y += 10.0
    wrap_and_draw_text(
        "Executive Summary:",
        fontname="helv",
        fontsize=11,
        leading=15,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    wrap_and_draw_text(
        "Data preparation occupies up to 80% of a data scientist's time, and arbitrary AI-based cleaning is often rejected due to lack of auditability. DataCleanAgent solves this by combining autonomous LLM reasoning with a deterministic, sandboxed execution registry. The platform profiles datasets against 6 dimensions of quality, plans and executes cleaning steps using a ReAct reasoning model, verifies each change against schema-drift limits, and outputs both professional DOCX audit reports and reproducible Python code.",
        fontname="helv",
        fontsize=9,
        leading=13,
        color=(0.20, 0.23, 0.27),
        style="normal"
    )
    
    # 2. Technology Stack Section
    y = page_height - margin - 300  # set starting position for next section on title page or start new page
    if y < 400.0:
        start_new_page()
    else:
        y += 20.0
        
    wrap_and_draw_text(
        "Technology Stack",
        fontname="helv",
        fontsize=16,
        leading=20,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    current_page.draw_line(
        fitz.Point(margin, y),
        fitz.Point(page_width - margin, y),
        color=(0.54, 0.36, 0.96),
        width=1.0
    )
    y += 10.0
    
    techs = [
        ("User Interface", "Streamlit (custom dark-mode glassmorphic cyber-aesthetic theme)"),
        ("AI Agent Brain", "Google Gemini 2.5 Flash (via structured JSON Outputs API)"),
        ("Database / Session Store", "SQLite (tracks historical cleaning sessions, action logs, and data quality states)"),
        ("Data Visualization", "Plotly (animated gauge indicators, dual-radar overlays, and column-level quality breakdown)"),
        ("Data Libraries", "Pandas, NumPy, Scikit-learn, and Difflib (fuzzy label normalization)"),
        ("Report Export", "python-docx (with custom professional typography and margins)"),
        ("QA Testing", "Python Unittest (48 automated test cases)")
    ]
    for category, desc in techs:
        wrap_and_draw_text(
            f"{category}: {desc}",
            fontname="helv",
            fontsize=10,
            leading=14,
            style="normal",
            bullet=True
        )
        
    # Start Section: MVP Scope vs Premium Extras
    start_new_page()
    wrap_and_draw_text(
        "MVP Scope vs. Premium Extras Added",
        fontname="helv",
        fontsize=16,
        leading=20,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    current_page.draw_line(
        fitz.Point(margin, y),
        fitz.Point(page_width - margin, y),
        color=(0.54, 0.36, 0.96),
        width=1.0
    )
    y += 10.0
    
    wrap_and_draw_text(
        "Core MVP Deliverables",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    mvps = [
        "6-Dimension Profiler evaluating Completeness, Uniqueness, Validity, Consistency, Accuracy, and Integrity.",
        "ReAct Agent Loop framework using Gemini to diagnose and clean tabular files.",
        "Deterministic Execution Registry decoupled from dangerous raw exec() commands.",
        "Basic Audit Trails and historical logging.",
        "Auto-Generated DOCX Report detailing quality checks and methodology."
    ]
    for item in mvps:
        wrap_and_draw_text(item, fontname="helv", fontsize=10, leading=14, bullet=True)
        
    y += 10.0
    wrap_and_draw_text(
        "Premium Extras (Wow Factor Additions)",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    extras = [
        "Unified Data Health Score Gauge: Animated Plotly dashboard chart showing aggregated quality scores (0-100%) and before/after improvements.",
        "Reproducible Python Script Export: Generates clean, production-ready pandas scripts to replicate the AI's actions.",
        "Multi-Step Session Rollback: Reverts data changes and Gemini chat memory dynamically.",
        "LLM Self-Healing Engine: Feeds execution errors back to the model to automatically re-plan with correct arguments.",
        "Data Drift Guardrails: Monitors and alerts on unexpected row-loss, column drop, or structural changes.",
        "Pre-Loaded Datasets: UCI Adult Income, Dirty Data Challenge REIN, OpenRefine, and Synthetic Messy Titanic built-in for instant demo validation."
    ]
    for item in extras:
        wrap_and_draw_text(item, fontname="helv", fontsize=10, leading=14, bullet=True)
        
    # Start Section: Detailed Feature List & Verification
    start_new_page()
    wrap_and_draw_text(
        "Detailed Feature List & Quality Metrics",
        fontname="helv",
        fontsize=16,
        leading=20,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    current_page.draw_line(
        fitz.Point(margin, y),
        fitz.Point(page_width - margin, y),
        color=(0.54, 0.36, 0.96),
        width=1.0
    )
    y += 10.0
    
    wrap_and_draw_text(
        "Data Quality Operations Suite",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    features = [
        "Median/Grouped Imputation: Auto-imputes missing values globally or based on subgroup averages.",
        "Fuzzy Category Normalization: Merges text typos and case inconsistencies (e.g. USA, U.S.A., usa -> USA).",
        "Outlier Clipping: Identifies and limits outliers using robust IQR and Z-Score thresholds.",
        "Range & Rule Clamping: Clips negative numeric fields to 0.0 and coerces invalid range records to Null.",
        "Encoding/Delimiter Ingestion: Automatically parses various CSV formats, BOMs, and separation tokens."
    ]
    for item in features:
        wrap_and_draw_text(item, fontname="helv", fontsize=10, leading=14, bullet=True)
        
    y += 15.0
    wrap_and_draw_text(
        "Security & AI Guardrails",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    wrap_and_draw_text(
        "To ensure corporate safety, the AI is completely decoupled from raw Python execution. It outputs structured JSON containing specific parameters that map to deterministic pre-vetted classes in the Action Registry. Argument validation happens in a sandbox layer, which immunizes the backend from prompt injection and code insertion vulnerabilities.",
        fontname="helv",
        fontsize=10,
        leading=14,
        style="normal"
    )
    
    y += 15.0
    wrap_and_draw_text(
        "QA Testing & Validation Metrics",
        fontname="helv",
        fontsize=12,
        leading=16,
        color=(0.06, 0.09, 0.16),
        style="bold"
    )
    wrap_and_draw_text(
        "The codebase includes a complete verification test suite containing 48 automated test cases covering profiling accuracy, action registry sanitization, persistence layers, and safety verifications. The success rate is 100% (48/48 tests passed).",
        fontname="helv",
        fontsize=10,
        leading=14,
        style="normal"
    )
    
    # Draw Page Numbers on all pages
    total_pages = doc.page_count
    for idx, page in enumerate(doc):
        # Draw on all pages
        page.insert_text(
            fitz.Point(page_width / 2.0 - 20, page_height - 30),
            f"Page {idx + 1} of {total_pages}",
            fontsize=8,
            fontname="helv",
            color=(0.36, 0.42, 0.50)
        )
        
    # Save Document
    pdf_path = "s:/GenAi_hackthon/data/hackathon_project_report.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    doc.save(pdf_path)
    doc.close()
    print(f"Successfully compiled professional PDF report to: {pdf_path}")

if __name__ == '__main__':
    create_report_pdf()
