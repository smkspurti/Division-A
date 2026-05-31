# modules/pdf_generator.py
# Generates a printable PDF from the application text

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
from datetime import date

def generate_pdf(data: dict, output_path: str = "outputs/mutation_application.pdf") -> str:
    """
    Creates a professional PDF file.
    Returns the path to the generated file.
    """
    os.makedirs("outputs", exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=60, leftMargin=60,
        topMargin=60, bottomMargin=60
    )

    # ── Styles ──
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title", fontSize=15, alignment=TA_CENTER,
        textColor=colors.HexColor("#1a5376"),
        fontName="Helvetica-Bold", spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        "subtitle", fontSize=10, alignment=TA_CENTER,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica", spaceAfter=2
    )
    normal_style = ParagraphStyle(
        "normal_custom", fontSize=10,
        fontName="Helvetica", spaceAfter=6, leading=16
    )
    bold_style = ParagraphStyle(
        "bold_custom", fontSize=10,
        fontName="Helvetica-Bold", spaceAfter=4
    )
    right_style = ParagraphStyle(
        "right_style", fontSize=9,
        fontName="Helvetica-Oblique",
        alignment=TA_RIGHT, spaceAfter=6
    )

    story = []
    mutation_type = data.get("mutation_type", "Sale")
    aadhaar = data.get("aadhaar", "000000000000")

    # ── Title ──
    story.append(Paragraph("GOVERNMENT OF KARNATAKA", title_style))
    story.append(Paragraph("Department of Revenue — Land Mutation Application", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a5376")))
    story.append(Spacer(1, 10))

    # ── Date ──
    story.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", right_style))
    story.append(Spacer(1, 6))

    # ── Addressee ──
    story.append(Paragraph("TO,", bold_style))
    story.append(Paragraph(f"The Tahsildar,<br/>{data.get('taluk','')} Taluk,<br/>{data.get('district','')} District, Karnataka.", normal_style))
    story.append(Spacer(1, 10))

    # ── Subject ──
    story.append(Paragraph(
        f"<b>SUBJECT:</b> Application for Land Mutation — {mutation_type} | Survey No. {data.get('survey_no','')}",
        normal_style
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 10))

    # ── Salutation ──
    story.append(Paragraph("Respected Sir/Madam,", normal_style))
    story.append(Paragraph(
        f"I, <b>{data.get('applicant_name','')}</b>, hereby submit this application for mutation "
        f"of land records in <b>{data.get('village','')}</b>, {data.get('taluk','')} Taluk, "
        f"{data.get('district','')} District, Karnataka.",
        normal_style
    ))
    story.append(Spacer(1, 10))

    # ── Property Details Table ──
    story.append(Paragraph("<b>PROPERTY DETAILS:</b>", bold_style))

    prop_data = [
        ["Survey Number", data.get("survey_no", "")],
        ["Village", data.get("village", "")],
        ["Taluk", data.get("taluk", "")],
        ["District", data.get("district", "")],
        ["Land Area", f"{data.get('land_area', '')} Acres"],
        ["Mutation Type", mutation_type],
    ]

    prop_table = Table(prop_data, colWidths=[2.2*inch, 3.8*inch])
    prop_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#d6e4f0")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#1a5376")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (1,0), (1,-1), [colors.white, colors.HexColor("#f5f9fc")]),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(prop_table)
    story.append(Spacer(1, 12))

    # ── Applicant Details Table ──
    story.append(Paragraph("<b>APPLICANT DETAILS:</b>", bold_style))

    app_data = [
        ["Full Name", data.get("applicant_name", "")],
        ["Aadhaar Number", f"XXXX-XXXX-{aadhaar[-4:]}"],
        ["Mobile Number", data.get("mobile", "")],
    ]

    app_table = Table(app_data, colWidths=[2.2*inch, 3.8*inch])
    app_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#d6e4f0")),
        ("TEXTCOLOR", (0,0), (0,-1), colors.HexColor("#1a5376")),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("PADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(app_table)
    story.append(Spacer(1, 12))

    # ── Declaration ──
    story.append(Paragraph(
        "I hereby declare that all the information provided above is true and correct "
        "to the best of my knowledge. All required supporting documents are enclosed "
        "with this application for your kind reference and necessary action.",
        normal_style
    ))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Kindly process this application at the earliest.", normal_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Yours faithfully,", normal_style))
    story.append(Spacer(1, 30))

    # ── Signature ──
    story.append(Paragraph(f"<b>{data.get('applicant_name','')}</b>", normal_style))
    story.append(Paragraph(f"Mobile: {data.get('mobile','')}", normal_style))
    story.append(Paragraph(f"Date: {date.today().strftime('%d/%m/%Y')}", normal_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 10))

    # ── Enclosures ──
    story.append(Paragraph("<b>ENCLOSURES:</b>", bold_style))
    from modules.checklist import get_required_documents
    docs = get_required_documents(mutation_type)
    for i, d in enumerate(docs, 1):
        story.append(Paragraph(f"{i}. {d}", normal_style))

    # ── Build PDF ──
    doc.build(story)
    return output_path