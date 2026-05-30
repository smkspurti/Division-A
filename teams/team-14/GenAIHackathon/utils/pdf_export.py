from fpdf import FPDF
import datetime

REPLACEMENTS = {
    "\u2014": "-", "\u2013": "-", "\u2018": "'", "\u2019": "'",
    "\u201c": '"', "\u201d": '"', "\u2022": "*", "\u2026": "...",
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u00b7": "*",
    "\u00e9": "e", "\u00e8": "e", "\u00ea": "e", "\u00eb": "e",
    "\u00e0": "a", "\u00e1": "a", "\u00e2": "a", "\u00e4": "a",
    "\u00f6": "o", "\u00fc": "u", "\u00df": "ss", "\u00f1": "n",
    "\u2192": "->", "\u2190": "<-", "\u2191": "^", "\u2193": "v",
    "\u00a9": "(c)", "\u00ae": "(R)", "\u2122": "(TM)",
}

def clean(text):
    if not isinstance(text, str):
        text = str(text)
    for k, v in REPLACEMENTS.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


class IdeaForgePDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(99, 102, 241)
        self.cell(0, 12, clean("IdeaForge AI - Project Report"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 6, clean(f"Generated on {datetime.datetime.now().strftime('%B %d, %Y at %H:%M')}"), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_draw_color(99, 102, 241)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 6, clean(f"IdeaForge AI | Page {self.page_no()}"), align="C")

    def section_title(self, title):
        self.ln(4)
        self.set_fill_color(240, 240, 255)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(60, 60, 180)
        self.cell(0, 9, clean(f"  {title}"), fill=True, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def body_text(self, text, indent=0):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        x = 10 + indent
        self.set_x(x)
        width = self.w - self.r_margin - x
        if width < 10:
            width = self.w - self.r_margin - 10
            self.set_x(10)
        self.multi_cell(width, 6, clean(text))

    def key_value(self, key, value):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.set_x(10)
        self.cell(40, 6, clean(f"{key}:"))
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        width = self.w - self.r_margin - 50
        self.multi_cell(width, 6, clean(str(value)))


def generate_pdf(student_data, ideas_data, skill_gap_data, roadmap_data, risk_data):
    pdf = IdeaForgePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Student Profile
    pdf.section_title("Student Profile")
    pdf.key_value("Name", student_data["name"])
    pdf.key_value("Skills", student_data["skills"])
    pdf.key_value("Domain", student_data["domain"])
    pdf.key_value("Tools", student_data["tools"])
    pdf.key_value("Duration", student_data["duration"])

    # Project Ideas
    pdf.section_title("Top 5 Project Ideas")
    page_w = pdf.w - pdf.l_margin - pdf.r_margin
    for idea in ideas_data.get("ideas", []):
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_text_color(99, 102, 241)
        pdf.set_x(10)
        pdf.multi_cell(page_w, 8, clean(f"#{idea['rank']} {idea['title']}  [Score: {idea['overall_score']}/10]"))
        pdf.set_text_color(40, 40, 40)
        pdf.body_text(idea["description"], indent=4)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.set_x(10)
        pdf.multi_cell(page_w, 5, clean(f"Tech: {', '.join(idea['tech_stack'])}   |   Dataset: {idea['dataset']}   |   Complexity: {idea['complexity']}"))
        pdf.set_x(10)
        pdf.multi_cell(page_w, 5, clean(f"Feasibility: {idea['feasibility_score']}/10   Innovation: {idea['innovation_score']}/10   Impact: {idea['impact_score']}/10"))
        pdf.ln(3)

    # Skill Gap
    pdf.section_title("Skill Gap Analysis")
    pdf.key_value("Readiness Score", f"{skill_gap_data.get('readiness_score', 'N/A')}%")
    pdf.key_value("Summary", skill_gap_data.get("summary", ""))
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_x(10)
    pdf.multi_cell(page_w, 7, clean("Skills You Have:"))
    pdf.body_text(", ".join(skill_gap_data.get("has_skills", [])), indent=4)
    if skill_gap_data.get("missing_skills"):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(10)
        pdf.multi_cell(page_w, 7, clean("Skills to Learn:"))
        for ms in skill_gap_data["missing_skills"]:
            pdf.body_text(f"* {ms['skill']} ({ms['importance']} priority) - Learn in {ms['learn_in']} via {ms['resource']}", indent=4)

    # Roadmap
    pdf.section_title("Project Roadmap")
    for week in roadmap_data.get("weeks", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(60, 60, 180)
        pdf.set_x(10)
        pdf.multi_cell(page_w, 7, clean(f"Week {week['week']}: {week['title']}"))
        pdf.set_text_color(40, 40, 40)
        pdf.body_text(f"Goal: {week['goal']}", indent=4)
        for task in week.get("tasks", []):
            pdf.body_text(f"* {task}", indent=8)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.body_text(f"Deliverable: {week['deliverable']}", indent=4)
        pdf.ln(2)

    # Risk Analysis
    pdf.section_title("Risk Analysis")
    pdf.key_value("Overall Risk", risk_data.get("overall_risk", "Medium"))
    for risk in risk_data.get("risks", []):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(180, 60, 60)
        pdf.set_x(10)
        pdf.multi_cell(page_w, 7, clean(f"[{risk['category']}] {risk['risk']}"))
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", "", 9)
        pdf.body_text(f"Probability: {risk['probability']}  |  Impact: {risk['impact']}  |  Mitigation: {risk['mitigation']}", indent=4)

    return bytes(pdf.output())
