# modules/validator.py
# This file validates all form inputs before generating the application

import re
from .language_manager import t

def validate_aadhaar(aadhaar: str) -> bool:
    """Check if Aadhaar number is exactly 12 digits"""
    return bool(re.match(r'^\d{12}$', aadhaar.strip()))

def validate_mobile(mobile: str) -> bool:
    """Check if mobile number is exactly 10 digits starting with 6-9"""
    return bool(re.match(r'^[6-9]\d{9}$', mobile.strip()))

def validate_survey_number(survey_no: str) -> bool:
    """Check if survey number is not empty and has valid format"""
    return bool(survey_no.strip()) and len(survey_no.strip()) >= 2

def validate_land_area(area) -> bool:
    """Check if land area is a positive number"""
    try:
        val = float(area)
        return 0.01 <= val <= 9999
    except:
        return False

def validate_form(data: dict) -> dict:
    """
    Main validation function.
    Takes form data as dictionary.
    Returns dict with:
      - is_valid: True/False
      - errors: list of error messages
      - warnings: list of warning messages
    """
    errors = []
    warnings = []

    # Check applicant name
    if not data.get("applicant_name", "").strip():
        errors.append(t("err_name_req"))
    elif len(data["applicant_name"].strip()) < 3:
        errors.append(t("err_name_len"))

    # Check Aadhaar
    if not data.get("aadhaar", "").strip():
        errors.append(t("err_aadhaar_req"))
    elif not validate_aadhaar(data["aadhaar"]):
        errors.append(t("err_aadhaar_len"))

    # Check Mobile
    if not data.get("mobile", "").strip():
        errors.append(t("err_mobile_req"))
    elif not validate_mobile(data["mobile"]):
        errors.append(t("err_mobile_len"))

    # Check Survey Number
    if not data.get("survey_no", "").strip():
        errors.append(t("err_survey_req"))
    elif not validate_survey_number(data["survey_no"]):
        errors.append(t("err_survey_fmt"))

    # Check District
    if not data.get("district", "").strip():
        errors.append(t("err_district_req"))

    # Check Taluk
    if not data.get("taluk", "").strip():
        errors.append(t("err_taluk_req"))

    # Check Village
    if not data.get("village", "").strip():
        errors.append(t("err_village_req"))

    # Check Land Area
    if not str(data.get("land_area", "")).strip():
        errors.append(t("err_area_req"))
    elif not validate_land_area(data["land_area"]):
        errors.append(t("err_area_fmt"))

    # Check Mutation Type
    if not data.get("mutation_type", "").strip():
        errors.append(t("err_mutation_req"))

    # Check Seller Name (required for Sale and Gift)
    if data.get("mutation_type") in ["Sale", "Gift", t("val_sale"), t("val_gift"), "ಮಾರಾಟ", "ಮಾರಾಟ (Sale)", "ಉಡುಗೊರೆ", "ಉಡುಗೊರೆ (Gift)"]:
        if not data.get("seller_name", "").strip():
            errors.append(t("err_seller_req"))

    # Check Buyer Name (required for Sale and Gift)
    if data.get("mutation_type") in ["Sale", "Gift", t("val_sale"), t("val_gift"), "ಮಾರಾಟ", "ಮಾರಾಟ (Sale)", "ಉಡುಗೊರೆ", "ಉಡುಗೊರೆ (Gift)"]:
        if not data.get("buyer_name", "").strip():
            errors.append(t("err_buyer_req"))

    # Warnings (non-blocking)
    if not data.get("uploaded_docs"):
        warnings.append(t("warn_no_docs"))

    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }