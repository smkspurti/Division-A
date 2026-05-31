"""
utils/translator.py
Translation using IndicTrans2 (AI4Bharat) approach.

IndicTrans2 is the state-of-the-art multilingual translation model by AI4Bharat
for Indic languages. The full model requires PyTorch + ~1GB weights, so we implement
it in two tiers:

  Tier 1 (primary):  AI4Bharat hosted inference API  — zero local GPU needed
  Tier 2 (fallback): deep-translator GoogleTranslator — always available

This is the recommended hackathon pattern when running without a GPU server.
Reference: https://github.com/AI4Bharat/IndicTrans2
"""

import requests
import time
from deep_translator import GoogleTranslator

# ── AI4Bharat IndicTrans2 API config ───────────────────────────────────────
_INDICTRANS2_API = "https://indic-translate.ai4bharat.org/translate"
_HEADERS = {"Content-Type": "application/json"}

# Language codes used by IndicTrans2 (Flores-200 format)
_LANG_CODE = {
    "kannada": "kan_Knda",
    "hindi":   "hin_Deva",
    "english": "eng_Latn",
}


def _indictrans2_api(text: str, src: str = "eng_Latn", tgt: str = "kan_Knda") -> str | None:
    """
    Call AI4Bharat's IndicTrans2 hosted API.
    Returns translated string or None on any failure.
    """
    try:
        payload = {
            "source_language": src,
            "target_language": tgt,
            "sentences": [text],
        }
        resp = requests.post(_INDICTRANS2_API, json=payload, headers=_HEADERS, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            # Response schema: {"translations": ["translated text"]}
            translations = data.get("translations") or data.get("output") or []
            if translations:
                return translations[0] if isinstance(translations[0], str) else translations[0].get("translated", "")
    except Exception:
        pass
    return None


def _google_fallback(text: str, src: str = "en", tgt: str = "kn") -> str:
    """GoogleTranslator fallback — splits into chunks to respect 5000-char limit."""
    chunks = [text[i:i+4500] for i in range(0, len(text), 4500)]
    translated = []
    for chunk in chunks:
        try:
            translated.append(GoogleTranslator(source=src, target=tgt).translate(chunk))
            time.sleep(0.2)   # be polite to the free API
        except Exception:
            translated.append(chunk)  # if a chunk fails, keep original
    return "\n\n".join(translated)


def translate_to_kannada(text: str) -> tuple[str, str]:
    """
    Translate English text to Kannada.
    Returns (translated_text, engine_used) where engine_used is
    'IndicTrans2 (AI4Bharat)' or 'Google Translate (fallback)'.
    """
    # Split into manageable chunks for IndicTrans2 API as well
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    results = []
    used_engine = "IndicTrans2 (AI4Bharat)"

    for chunk in chunks:
        result = _indictrans2_api(chunk)
        if result:
            results.append(result)
        else:
            # IndicTrans2 API unavailable — use Google as fallback
            used_engine = "Google Translate (fallback)"
            results.append(_google_fallback(chunk))

    return "\n\n".join(results), used_engine