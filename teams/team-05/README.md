# Personal Finance Health Report Generator

A GenAI system that takes structured personal financial data and generates a personalised monthly Financial Health Report with a Wellness Score, spending analysis, and AI-prioritised recommendations.

**Built for:** GenAI Hackathon · Domain 5: Finance & Banking AI · Team A5

---

## What it does

1. User fills in monthly income, expenses, EMIs, savings, and investments
2. Compute a **Financial Wellness Score (0-100)** broken into 5 components — deterministic, no LLM in this step
3. Visualise spending vs Indian household benchmarks (NSSO 68th Round derived)
4. LLM (Groq · Llama 3.3 70B) generates a spending-pattern narrative
5. LLM generates 3 prioritised, actionable recommendations as structured JSON
6. Assemble everything into a downloadable **DOCX report**

---

## Quickstart

### 1. Get a Groq API key (free, ~60 seconds)

Go to [console.groq.com/keys](https://console.groq.com/keys), sign in with Google, click "Create API Key". No credit card needed.

### 2. Set up the project

```bash
git clone <your-repo>
cd teams/team-05/app/finance-health-app

python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and paste your Groq key in GROQ_API_KEY
```

### 3. Run

```bash
streamlit run app.py
```

App opens at `http://localhost:8501`.

Click **"Load sample profile"** in the sidebar to pre-fill realistic data for a quick demo.

### 4. Run tests

```bash
pytest -q
```

---

## Project structure

```
finance-health-app/
├── app.py              # Streamlit UI — single entrypoint
├── models.py           # Pydantic models (input validation + output contracts)
├── score.py            # Wellness Score engine — pure functions, fully tested
├── benchmarks.py       # Hardcoded Indian household spending benchmarks
├── llm.py              # Groq client wrapper with retry + fallback
├── report.py           # DOCX report generator (python-docx)
├── prompts/
│   ├── narrative.txt        # System prompt: spending-pattern narrative
│   └── recommendations.txt  # System prompt: 3 structured recommendations
├── data/
│   └── sample_profile.json  # Test profile (auto-fills the form)
├── tests/
│   └── test_score.py        # Unit tests for the scoring engine
├── requirements.txt
├── .env.example
└── README.md
```

---

## Wellness Score components

| Component | Max | What it measures |
|---|---|---|
| Savings Rate | 25 | (Income − Expenses − EMI) / Income |
| Debt-to-Income | 25 | Total monthly EMI / Income |
| Emergency Fund | 20 | Liquid savings / monthly outflow (months covered) |
| Investments | 15 | Volume (vs age-adjusted target) + diversification across categories |
| Discretionary Control | 15 | (Entertainment + Shopping) / Income |

Thresholds in `benchmarks.py::ADVISABLE_THRESHOLDS`. Tunable without touching `score.py`.

---

## Datasets used

**Primary:** [Open Finance Synthetic Dataset (Plaid)](https://www.kaggle.com/datasets/apoorvwatsky/bank-transaction-data) — synthetic US bank transactions, used for transaction-pattern reference.

**Indian context benchmarks:** Aggregate household spending percentages derived from public summaries of NSSO 68th Round Consumer Expenditure Survey and RBI DBIE Household Financial Savings data. Hardcoded in `benchmarks.py` — teammate to refresh from latest MOSPI/RBI publications.

---

## Architecture

```
   [Streamlit form] ───► FinancialProfile (Pydantic) ───► compute_wellness_score()
                                                              │
                                                              ▼
                                                       WellnessScore + components
                                                              │
                            ┌─────────────────────────────────┼───────────────┐
                            ▼                                 ▼               ▼
                 generate_narrative()              generate_recommendations()  Plotly charts
                 (Groq · Llama 3.3 70B)            (Groq · JSON mode)          (gauge, donut, bar)
                            │                                 │               │
                            └──────────────┬──────────────────┘               │
                                           ▼                                  │
                                    build_report() ◄──────────────────────────┘
                                           │
                                           ▼
                                    DOCX download
```

---

## Production-readiness notes

- **Input validation:** Every field passes through Pydantic. Bad inputs are rejected before they hit the engine.
- **Deterministic core:** The score never depends on the LLM. If Groq is down, you still get the score, the charts, and a fallback report.
- **Caching:** LLM calls cached by profile hash (`@st.cache_data`). Re-submitting the same data costs zero quota.
- **Retry + fallback:** LLM calls retry once on transient errors, then fall back to deterministic explanations. The app never breaks mid-demo.
- **Secrets:** `.env` is gitignored; `.env.example` documents required keys.
- **Logging:** Standard `logging` at INFO level. Failed chart exports, LLM errors, etc. all logged.

---

## License

Built for academic competition use. Not financial advice. Always consult a SEBI-registered advisor for actual financial decisions.
