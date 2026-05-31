# 🧬 TrialMatch AI — Clinical Trial Eligibility Screener

**Problem Statement A13 · Healthcare & Medical AI [CO3/CO4]**

> A GenAI system that takes a patient's EHR summary and a set of clinical trial eligibility criteria, and produces a structured eligibility report with criterion-level Match/No Match/Uncertain decisions and rationale.

---

## 🚀 Quick Start

### 1. Get a FREE Gemini API Key
Visit https://ai.google.dev and create a free API key.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set API Key
```bash
# Option A: Set as environment variable
set GEMINI_API_KEY=your_key_here   # Windows

# Option B: Create .env file
copy .env.example .env
# Edit .env and add your key
```

### 4. Run the App
```bash
streamlit run app.py
```

---

## 📋 Features

| Feature | Status |
|---------|--------|
| Patient EHR text input | ✅ |
| PDF EHR upload | ✅ |
| Trial criteria text input | ✅ |
| Criterion-level decision table (Match/No Match/Uncertain) | ✅ |
| Natural language rationale for each decision | ✅ |
| Confidence scores per criterion | ✅ |
| Summary eligibility report (DOCX export) | ✅ |
| CSV export of decision table | ✅ |
| 3+ pre-loaded demo patient–trial pairs | ✅ |
| Session history tracking | ✅ |

---

## 🏗 Architecture

```
app.py (Streamlit UI)
└── engine/
    ├── criterion_parser.py   → Parse trial criteria → structured list (Gemini LLM)
    ├── ehr_parser.py         → Extract clinical facts from EHR (Gemini LLM)
    ├── eligibility_matcher.py → Per-criterion Match/No Match/Uncertain (Gemini LLM)
    └── report_generator.py  → Generate professional DOCX report (python-docx)
data/
    ├── sample_ehrs/          → 3 real-world inspired patient EHR summaries
    └── sample_trials/        → 3 clinical trial criteria (ClinicalTrials.gov)
```

---

## 🧪 Demo Cases (Pre-loaded)

| Patient | Condition | Trial |
|---------|-----------|-------|
| PT-001 (Male, 65yr) | Type 2 Diabetes, HbA1c 8.2% | GLP-1 Phase III (Semaglutide) |
| PT-002 (Female, 47yr) | Breast Cancer Stage IIA, BRCA1+ | PARP Inhibitor + Pembrolizumab |
| PT-003 (Male, 73yr) | Mild-to-Moderate Alzheimer's | Anti-Amyloid Antibody Phase III |

---

## 📊 Public Datasets Used

- **ClinicalTrials.gov**: Eligibility criteria sourced from publicly available trial designs
  - SUSTAIN/STEP trial framework (NCT semaglutide)
  - OlympiA/KEYNOTE trial framework (BRCA+ breast cancer)
  - CLARITY-AD trial framework (Lecanemab/Alzheimer's)
- **MIMIC-III Inspired**: EHR summaries based on published MIMIC-III clinical note structure

---

## 🛠 Tech Stack

- **LLM**: Google Gemini 1.5 Flash (free tier — no paid OpenAI APIs)
- **UI**: Streamlit
- **Orchestration**: LangChain-inspired pipeline
- **PDF**: PyPDF2
- **Reports**: python-docx
- **Data**: pandas

---

## ⚖️ Decision Logic

```
If ANY exclusion criterion → MATCH → NOT ELIGIBLE
If ANY inclusion criterion → NO MATCH → NOT ELIGIBLE  
If >40% criteria → UNCERTAIN → FURTHER REVIEW NEEDED
Otherwise → POTENTIALLY ELIGIBLE
```

---

## 📝 Disclaimer

This tool is for research and educational purposes only. All eligibility decisions must be verified by a qualified clinical investigator. This does not constitute medical advice.

---

*Hackathon A13 · Healthcare & Medical AI · Built during 12-hour hackathon*
