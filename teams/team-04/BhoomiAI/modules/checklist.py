# modules/checklist.py
# Generates smart document checklist based on mutation type

import pandas as pd
import os

def get_required_documents(mutation_type: str) -> list:
    """
    Returns list of required documents for given mutation type.
    Reads from document_requirements.csv
    """
    try:
        # Load the CSV file
        csv_path = os.path.join("data", "document_requirements.csv")
        df = pd.read_csv(csv_path)

        # Find the row matching mutation type
        row = df[df["mutation_type"] == mutation_type]

        if row.empty:
            return get_default_documents(mutation_type)

        # Documents are separated by semicolons in the CSV
        docs_str = row.iloc[0]["required_documents"]
        docs_list = [doc.strip() for doc in docs_str.split(";")]
        return docs_list

    except Exception as e:
        print(f"Error loading documents: {e}")
        return get_default_documents(mutation_type)


def get_default_documents(mutation_type: str) -> list:
    """Fallback document list if CSV fails"""
    defaults = {
        "Sale": [
            "Sale Deed (Registered)",
            "RTC Copy",
            "Aadhaar Card of Buyer",
            "Aadhaar Card of Seller",
            "Latest Tax Receipt",
            "Encumbrance Certificate"
        ],
        "Inheritance": [
            "Death Certificate",
            "Legal Heir Certificate",
            "RTC Copy",
            "Aadhaar Card of Legal Heirs",
            "Family Tree Document",
            "Affidavit"
        ],
        "Gift": [
            "Gift Deed (Registered)",
            "RTC Copy",
            "Aadhaar Card of Donor",
            "Aadhaar Card of Recipient",
            "Relationship Proof",
            "Tax Receipt"
        ]
    }
    return defaults.get(mutation_type, ["RTC Copy", "Aadhaar Card", "Tax Receipt"])


def generate_checklist(mutation_type: str, uploaded_docs: list) -> dict:
    """
    Compares required documents vs uploaded documents.
    Returns:
      - required: all required docs
      - uploaded: docs user has uploaded
      - missing: docs still needed
      - completion_percent: how complete the submission is
    """
    required = get_required_documents(mutation_type)

    # Normalize names for comparison
    uploaded_lower = [doc.lower().strip() for doc in uploaded_docs]

    missing = []
    present = []

    for doc in required:
        # Check if any uploaded doc name matches
        found = any(doc.lower() in u or u in doc.lower() for u in uploaded_lower)
        if found:
            present.append(doc)
        else:
            missing.append(doc)

    total = len(required)
    done = len(present)
    percent = int((done / total) * 100) if total > 0 else 0

    return {
        "required": required,
        "present": present,
        "missing": missing,
        "completion_percent": percent,
        "is_complete": len(missing) == 0
    }


def get_processing_info(mutation_type: str) -> dict:
    """Returns processing time and authority for mutation type"""
    try:
        csv_path = os.path.join("data", "document_requirements.csv")
        df = pd.read_csv(csv_path)
        row = df[df["mutation_type"] == mutation_type]

        if not row.empty:
            return {
                "processing_days": int(row.iloc[0]["processing_days"]),
                "authority": row.iloc[0]["authority"]
            }
    except:
        pass

    return {"processing_days": 30, "authority": "Tahsildar Office"}