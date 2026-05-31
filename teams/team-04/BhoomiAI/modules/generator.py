# modules/generator.py
# Generates the formal mutation application text using templates + AI logic

import pandas as pd
import os
from datetime import date

def load_templates() -> dict:
    """Load mutation templates from CSV"""
    try:
        csv_path = os.path.join("data", "mutation_templates.csv")
        df = pd.read_csv(csv_path)
        templates = {}
        for _, row in df.iterrows():
            templates[row["mutation_type"]] = {
                "subject": row["application_subject"],
                "reason": row["application_reason"]
            }
        return templates
    except Exception as e:
        print(f"Template load error: {e}")
        return {}


def generate_application(data: dict) -> str:
    """
    Generates a formal government-style mutation application.
    Uses template + form data to build the full application text.
    """
    templates = load_templates()
    mutation_type = data.get("mutation_type", "Sale")
    today = date.today().strftime("%d/%m/%Y")

    # Get template for this mutation type
    template = templates.get(mutation_type, {
        "subject": f"Request for Mutation after {mutation_type}",
        "reason": f"Ownership transferred through {mutation_type.lower()}"
    })

    # Build seller/buyer section based on mutation type
    if mutation_type == "Sale":
        transaction_section = f"""
The land was purchased from Seller: {data.get('seller_name', 'N/A')} 
through a registered Sale Deed. The buyer {data.get('buyer_name', 'N/A')} 
is now the rightful owner of the said property and requests mutation of 
land records accordingly.
""".strip()

    elif mutation_type == "Inheritance":
        transaction_section = f"""
The applicant is the legal heir of the deceased previous owner. 
The ownership has been transferred through legal inheritance as per 
the family tree and legal heir certificate submitted along with this application.
""".strip()

    elif mutation_type == "Gift":
        transaction_section = f"""
The land was received as a Gift from Donor: {data.get('seller_name', 'N/A')} 
through a registered Gift Deed. The recipient {data.get('buyer_name', 'N/A')} 
requests mutation of land records in their name accordingly.
""".strip()
    else:
        transaction_section = "The ownership has been transferred as per attached documents."

    # Build the full application
    application = f"""
TO,
The Tahsildar,
{data.get('taluk', '')} Taluk,
{data.get('district', '')} District,
Karnataka — 560001

Date: {today}

SUBJECT: {template['subject']} — Survey No. {data.get('survey_no', '')}

Respected Sir/Madam,

I, {data.get('applicant_name', '')}, Son/Daughter/Wife of _____________, 
aged _____ years, residing at {data.get('village', '')}, {data.get('taluk', '')} Taluk, 
{data.get('district', '')} District, Karnataka, do hereby submit this application 
for mutation of land records.

PROPERTY DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Survey Number   : {data.get('survey_no', '')}
  Village         : {data.get('village', '')}
  Taluk           : {data.get('taluk', '')}
  District        : {data.get('district', '')}
  Land Area       : {data.get('land_area', '')} Acres
  Mutation Type   : {mutation_type}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APPLICANT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Name            : {data.get('applicant_name', '')}
  Aadhaar Number  : XXXX-XXXX-{data.get('aadhaar', '')[-4:]}
  Mobile Number   : {data.get('mobile', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REASON FOR MUTATION:
{transaction_section}

I hereby declare that all the information provided above is true and 
correct to the best of my knowledge. All required supporting documents 
are enclosed with this application for your kind reference and necessary action.

I kindly request your good office to process this mutation application 
at the earliest and update the land records accordingly.

Thanking you,

Yours faithfully,


________________________
{data.get('applicant_name', '')}
Aadhaar: XXXX-XXXX-{data.get('aadhaar', '')[-4:]}
Mobile: {data.get('mobile', '')}
Date: {today}

ENCLOSURES:
""".strip()

    # Add document list at bottom
    from modules.checklist import get_required_documents
    docs = get_required_documents(mutation_type)
    for i, doc in enumerate(docs, 1):
        application += f"\n  {i}. {doc}"

    return application


def get_sample_record(district: str = None) -> dict:
    """Load a sample record from the big dataset for demo purposes"""
    try:
        csv_path = os.path.join("data", "karnataka_land_records_29495.csv")
        df = pd.read_csv(csv_path)

        if district:
            filtered = df[df["district"] == district]
            if not filtered.empty:
                row = filtered.sample(1).iloc[0]
            else:
                row = df.sample(1).iloc[0]
        else:
            row = df.sample(1).iloc[0]

        return {
            "applicant_name": str(row.get("buyer_name", "")),
            "survey_no": str(row.get("survey_no", "")),
            "district": str(row.get("district", "")),
            "taluk": str(row.get("taluk", "")),
            "village": str(row.get("village", "")),
            "land_area": str(row.get("land_area_acres", "")),
            "mutation_type": str(row.get("mutation_type", "Sale")),
            "seller_name": str(row.get("seller_name", "")),
            "buyer_name": str(row.get("buyer_name", "")),
            "aadhaar": str(row.get("aadhaar_no", "000000000000")),
            "mobile": str(row.get("mobile_no", "9000000000"))
        }
    except Exception as e:
        print(f"Sample record error: {e}")
        return {}