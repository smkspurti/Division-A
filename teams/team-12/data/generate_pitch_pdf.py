import fitz  # PyMuPDF
import sys
import os

def create_pitch_pdf():
    # Initialize Document
    doc = fitz.open()
    
    # Page size A4 Landscape: 841.89 x 595.27 points
    page_width = 841.89
    page_height = 595.27
    
    margin = 60.0
    
    def start_slide(slide_num, title):
        # Create new landscape page
        page = doc.new_page(width=page_width, height=page_height)
        
        # Draw top banner line
        page.draw_line(
            fitz.Point(margin, 40),
            fitz.Point(page_width - margin, 40),
            color=(0.54, 0.36, 0.96), # purple accent
            width=3.0
        )
        
        # Slide number
        page.insert_text(
            fitz.Point(margin, 30),
            f"SLIDE {slide_num}",
            fontsize=10,
            fontname="hebo",
            color=(0.54, 0.36, 0.96)
        )
        
        # Slide Header Title
        page.insert_text(
            fitz.Point(margin + 60, 30),
            title.upper(),
            fontsize=11,
            fontname="hebo",
            color=(0.06, 0.09, 0.16)
        )
        
        # Draw side-layout guide vertical line
        page.draw_line(
            fitz.Point(280, 80),
            fitz.Point(280, page_height - 60),
            color=(0.90, 0.92, 0.94),
            width=1.0
        )
        
        # Footer
        page.draw_line(
            fitz.Point(margin, page_height - 45),
            fitz.Point(page_width - margin, page_height - 45),
            color=(0.90, 0.92, 0.94),
            width=0.75
        )
        page.insert_text(
            fitz.Point(margin, page_height - 30),
            "DataCleanAgent | Pitch Deck Guide",
            fontsize=8,
            fontname="helv",
            color=(0.36, 0.42, 0.50)
        )
        page.insert_text(
            fitz.Point(page_width - margin - 50, page_height - 30),
            f"Page {slide_num} / 6",
            fontsize=8,
            fontname="helv",
            color=(0.36, 0.42, 0.50)
        )
        
        return page

    def draw_left_panel(page, headline, subtext):
        # Draw a big bold statement on the left panel
        y = 110.0
        words = headline.split(" ")
        lines = []
        curr = []
        for w in words:
            test = " ".join(curr + [w])
            if fitz.get_text_length(test, fontname="hebo", fontsize=20) <= 200:
                curr.append(w)
            else:
                if curr:
                    lines.append(" ".join(curr))
                curr = [w]
        if curr:
            lines.append(" ".join(curr))
            
        for line in lines:
            page.insert_text(fitz.Point(margin, y), line, fontsize=20, fontname="hebo", color=(0.06, 0.09, 0.16))
            y += 24.0
            
        y += 10.0
        # Draw subtext under the left headline
        words_sub = subtext.split(" ")
        lines_sub = []
        curr_sub = []
        for w in words_sub:
            test = " ".join(curr_sub + [w])
            if fitz.get_text_length(test, fontname="helv", fontsize=10) <= 200:
                curr_sub.append(w)
            else:
                if curr_sub:
                    lines_sub.append(" ".join(curr_sub))
                curr_sub = [w]
        if curr_sub:
            lines_sub.append(" ".join(curr_sub))
            
        for line in lines_sub:
            page.insert_text(fitz.Point(margin, y), line, fontsize=10, fontname="helv", color=(0.36, 0.42, 0.50))
            y += 14.0

    def draw_right_bullets(page, bullets):
        y = 110.0
        for title, desc in bullets:
            # Bullet title (bold)
            page.insert_text(
                fitz.Point(310, y),
                "• " + title,
                fontsize=13,
                fontname="hebo",
                color=(0.54, 0.36, 0.96)
            )
            y += 18.0
            
            # Wrap bullet description text
            words = desc.split(" ")
            lines = []
            curr = []
            for w in words:
                test = " ".join(curr + [w])
                if fitz.get_text_length(test, fontname="helv", fontsize=11) <= 460:
                    curr.append(w)
                else:
                    if curr:
                        lines.append(" ".join(curr))
                    curr = [w]
            if curr:
                lines.append(" ".join(curr))
                
            for line in lines:
                page.insert_text(fitz.Point(322, y), line, fontsize=11, fontname="helv", color=(0.20, 0.23, 0.27))
                y += 15.0
            y += 12.0

    # ==================== SLIDE 1 ====================
    # Custom Title slide
    page1 = doc.new_page(width=page_width, height=page_height)
    # Background fill
    page1.draw_rect(fitz.Rect(0, 0, page_width, page_height), color=(0.06, 0.09, 0.16), fill=(0.06, 0.09, 0.16))
    
    # Accent color block
    page1.draw_rect(fitz.Rect(0, 0, 240, page_height), color=(0.09, 0.13, 0.24), fill=(0.09, 0.13, 0.24))
    page1.draw_line(fitz.Point(240, 0), fitz.Point(240, page_height), color=(0.54, 0.36, 0.96), width=3.0)
    
    # Title text
    page1.insert_text(fitz.Point(280, 220), "DATACLEANAGENT", fontsize=44, fontname="hebo", color=(1.0, 1.0, 1.0))
    page1.insert_text(fitz.Point(280, 265), "Cleaning Messy Data in Seconds with Safe, Trustworthy AI", fontsize=16, fontname="helv", color=(0.85, 0.87, 0.90))
    page1.insert_text(fitz.Point(280, 320), "Judge Pitch Guide & Live Demo Cheat Sheet", fontsize=13, fontname="hebo", color=(0.54, 0.36, 0.96))
    
    # Metadata left side
    page1.insert_text(fitz.Point(40, 180), "PITCH DECK", fontsize=14, fontname="hebo", color=(0.54, 0.36, 0.96))
    page1.insert_text(fitz.Point(40, 210), "Hackathon Presentation", fontsize=9, fontname="helv", color=(0.70, 0.74, 0.80))
    page1.insert_text(fitz.Point(40, 230), "Simple English Edition", fontsize=9, fontname="helv", color=(0.70, 0.74, 0.80))
    
    page1.insert_text(fitz.Point(40, page_height - 80), "Author: Rohi-21", fontsize=9, fontname="helv", color=(0.70, 0.74, 0.80))
    page1.insert_text(fitz.Point(40, page_height - 60), "May 2026", fontsize=9, fontname="helv", color=(0.70, 0.74, 0.80))

    # ==================== SLIDE 2 ====================
    page2 = start_slide(2, "The Problem")
    draw_left_panel(
        page2,
        "Dirty Data is a Nightmare",
        "Why businesses struggle to use raw data and why AI cleaning tools are often rejected."
    )
    draw_right_bullets(page2, [
        ("Data scientists waste 80% of their time", "They spend hours manually fixing typos, handling missing values, and clipping outliers instead of building models."),
        ("Traditional tools are a Black Box", "Standard AI cleaning tools just return the cleaned file. You don't know what they changed, what they deleted, or if they altered critical details."),
        ("No Trust = No Adoption", "If companies cannot see the exact mathematical steps the AI took, they cannot verify it and will not deploy it to production.")
    ])

    # ==================== SLIDE 3 ====================
    page3 = start_slide(3, "The Solution")
    draw_left_panel(
        page3,
        "Safe and Smart AI",
        "How DataCleanAgent bridges the gap between intelligence, safety, and transparency."
    )
    draw_right_bullets(page3, [
        ("Step 1: Multi-Dimensional Profiling", "Checks your dataset against 6 core quality metrics (Completeness, Uniqueness, Validity, Consistency, Accuracy, Integrity)."),
        ("Step 2: AI Planning (ReAct loop)", "The AI inspects the errors, plans the correct cleaning action, and executes it step-by-step."),
        ("Step 3: Deterministic Action Registry", "The AI cannot run arbitrary code on your PC. It only selects from pre-built, safe python actions (like mode-imputation, outliers clipping, etc.)."),
        ("Step 4: Safety Verifier", "Ensures the AI doesn't accidentally change the schema or drop too many rows. If a step fails, the AI self-heals and corrects it.")
    ])

    # ==================== SLIDE 4 ====================
    page4 = start_slide(4, "Key Features (WOW Factors)")
    draw_left_panel(
        page4,
        "Premium Extras that Wow",
        "Features we added to prove this is an enterprise-ready product, not just a toy."
    )
    draw_right_bullets(page4, [
        ("Unified Data Health Score Gauge", "A live Plotly dial that visualizes the dataset health rating from 0-100%. Watch the needle move from 'Before' to 'After' during the cleaning process!"),
        ("Download Reproducible Python Script", "Generates the exact, standalone pandas code the AI applied. Data engineers can download and run this script locally in their systems."),
        ("Session Rollback Support", "Interactively reverse any cleaning step. If the user doesn't like a change, one click rolls back the data and the AI's chat memory.")
    ])

    # ==================== SLIDE 5 ====================
    page5 = start_slide(5, "Live Demo Cheat Sheet")
    draw_left_panel(
        page5,
        "Winning Over the Judges",
        "A step-by-step walkthrough to showcase the platform's power in a live presentation."
    )
    draw_right_bullets(page5, [
        ("1. Ingestion: Upload the test dataset", "Choose 'Upload CSV File' and upload 'random_dirty_sales.csv' from your local data folder to show a raw, dirty file."),
        ("2. Run the Loop: AI in action", "Click 'Run Cleaning Loop'. Point to the terminal output showing the AI reasoning, self-healing, and applying sanitization steps."),
        ("3. Dashboard Comparison: Tab 3", "Click 'Tab 3: Compare'. Show the health gauge score jump (e.g. from 62% to 98%) and explain the radar chart overlay."),
        ("4. Code Export: Transparency", "Scroll down to 'Audit & Export' and download the Python Script. Show the judges the clean pandas code generated on the fly.")
    ])

    # ==================== SLIDE 6 ====================
    page6 = start_slide(6, "Architecture & Security")
    draw_left_panel(
        page6,
        "Behind the Scenes",
        "The technical foundation that ensures the application is secure, fast, and bulletproof."
    )
    draw_right_bullets(page6, [
        ("Tech Stack", "Streamlit for front-end, Google Gemini 2.5 Flash for reasoning, SQLite for sessions, and Plotly for visualizations."),
        ("100% Secure Design", "Immune to code injection because the LLM is restricted to calling registry arguments. No raw python string executions are allowed."),
        ("Enterprise Stability", "A comprehensive testing suite with 48/48 automated unit tests fully passing. Robust error handling ensures the app never crashes.")
    ])

    # Save
    pdf_path = "s:/GenAi_hackthon/data/hackathon_pitch_guide.pdf"
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    doc.save(pdf_path)
    doc.close()
    print(f"Successfully compiled pitch guide PDF to: {pdf_path}")

if __name__ == '__main__':
    create_pitch_pdf()
