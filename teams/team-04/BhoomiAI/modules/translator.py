# modules/translator.py
# Translates English application to Kannada
# Uses a template-based approach (no GPU needed, works offline)

def translate_to_kannada(data: dict) -> str:
    """
    Generates a Kannada mutation application using pre-translated templates.
    This approach works without any internet or GPU — perfect for hackathon.
    """

    mutation_type = data.get("mutation_type", "Sale")
    aadhaar = data.get("aadhaar", "000000000000")

    # Kannada translations for mutation types
    mutation_kannada = {
        "Sale":        "ಮಾರಾಟ (Sale)",
        "Inheritance": "ಉತ್ತರಾಧಿಕಾರ (Inheritance)",
        "Gift":        "ಉಡುಗೊರೆ (Gift)"
    }

    # Kannada transaction reason
    reason_kannada = {
        "Sale": (
            f"ಈ ಜಮೀನನ್ನು ವಿಕ್ರಯಕಾರ {data.get('seller_name','N/A')} ಅವರಿಂದ "
            f"ನೋಂದಾಯಿತ ಮಾರಾಟ ಪತ್ರದ ಮೂಲಕ ಖರೀದಿಸಲಾಗಿದೆ. "
            f"ಖರೀದಿದಾರ {data.get('buyer_name','N/A')} ಅವರು ಈ ಆಸ್ತಿಯ ನ್ಯಾಯಸಮ್ಮತ ಮಾಲೀಕರಾಗಿದ್ದಾರೆ."
        ),
        "Inheritance": (
            "ಅರ್ಜಿದಾರರು ಹಿಂದಿನ ಮಾಲೀಕರ ಕಾನೂನು ಉತ್ತರಾಧಿಕಾರಿಯಾಗಿದ್ದಾರೆ. "
            "ಕುಟುಂಬ ವೃಕ್ಷ ಮತ್ತು ಕಾನೂನು ಉತ್ತರಾಧಿಕಾರ ಪ್ರಮಾಣಪತ್ರದ ಆಧಾರದ ಮೇಲೆ "
            "ಮಾಲೀಕತ್ವ ವರ್ಗಾವಣೆಯಾಗಿದೆ."
        ),
        "Gift": (
            f"ಈ ಜಮೀನನ್ನು ದಾನಿ {data.get('seller_name','N/A')} ಅವರಿಂದ "
            f"ನೋಂದಾಯಿತ ಉಡುಗೊರೆ ಪತ್ರದ ಮೂಲಕ ಪಡೆಯಲಾಗಿದೆ. "
            f"ಸ್ವೀಕರಿಸುವವರು {data.get('buyer_name','N/A')} ಅವರ ಹೆಸರಿನಲ್ಲಿ ದಾಖಲೆ ಬದಲಾಯಿಸಬೇಕಾಗಿದೆ."
        )
    }

    from datetime import date
    today = date.today().strftime("%d/%m/%Y")

    application_kannada = f"""
ಸೇವೆಯಲ್ಲಿ,
ತಹಸೀಲ್ದಾರರು,
{data.get('taluk', '')} ತಾಲೂಕು,
{data.get('district', '')} ಜಿಲ್ಲೆ,
ಕರ್ನಾಟಕ ರಾಜ್ಯ

ದಿನಾಂಕ: {today}

ವಿಷಯ: ಜಮೀನು ಮ್ಯುಟೇಶನ್ ಅರ್ಜಿ — ಸರ್ವೇ ನಂ. {data.get('survey_no', '')}

ಮಾನ್ಯರೇ,

ನಾನು, {data.get('applicant_name', '')}, ಈ ಮೂಲಕ ಜಮೀನು ದಾಖಲೆಗಳ ಮ್ಯುಟೇಶನ್‌ಗಾಗಿ
ಈ ಅರ್ಜಿಯನ್ನು ಸಲ್ಲಿಸುತ್ತಿದ್ದೇನೆ.

ಆಸ್ತಿ ವಿವರಗಳು:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ಸರ್ವೇ ನಂಬರ್     : {data.get('survey_no', '')}
  ಗ್ರಾಮ            : {data.get('village', '')}
  ತಾಲೂಕು          : {data.get('taluk', '')}
  ಜಿಲ್ಲೆ            : {data.get('district', '')}
  ಜಮೀನಿನ ವಿಸ್ತೀರ್ಣ : {data.get('land_area', '')} ಎಕರೆ
  ಮ್ಯುಟೇಶನ್ ವಿಧ    : {mutation_kannada.get(mutation_type, mutation_type)}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ಅರ್ಜಿದಾರರ ವಿವರಗಳು:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ಹೆಸರು           : {data.get('applicant_name', '')}
  ಆಧಾರ್ ಸಂಖ್ಯೆ    : XXXX-XXXX-{aadhaar[-4:]}
  ಮೊಬೈಲ್ ಸಂಖ್ಯೆ   : {data.get('mobile', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ಮ್ಯುಟೇಶನ್ ಕಾರಣ:
{reason_kannada.get(mutation_type, 'ದಾಖಲೆಗಳ ಪ್ರಕಾರ ಮಾಲೀಕತ್ವ ವರ್ಗಾವಣೆಯಾಗಿದೆ.')}

ಮೇಲ್ಕಂಡ ಎಲ್ಲಾ ಮಾಹಿತಿಯು ನನ್ನ ಅರಿವಿನ ಪ್ರಕಾರ ಸತ್ಯ ಮತ್ತು ನಿಖರವಾಗಿದೆ ಎಂದು
ಘೋಷಿಸುತ್ತೇನೆ. ಅಗತ್ಯ ದಾಖಲೆಗಳನ್ನು ಈ ಅರ್ಜಿಯೊಂದಿಗೆ ಲಗತ್ತಿಸಲಾಗಿದೆ.

ದಯವಿಟ್ಟು ಈ ಅರ್ಜಿಯನ್ನು ಶೀಘ್ರವಾಗಿ ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಿ ಜಮೀನು ದಾಖಲೆಗಳನ್ನು
ನವೀಕರಿಸಬೇಕೆಂದು ವಿನಂತಿಸುತ್ತೇನೆ.

ತಮ್ಮ ವಿಶ್ವಾಸಿ,


________________________
{data.get('applicant_name', '')}
ಮೊಬೈಲ್: {data.get('mobile', '')}
ದಿನಾಂಕ: {today}
"""
    return application_kannada