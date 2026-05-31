"""
Groq client wrapper.

Wraps two functions the app actually needs:
    generate_narrative(profile, score)         -> str
    generate_recommendations(profile, score)   -> RecommendationSet

Both:
  - Load prompts from prompts/*.txt (so teammates can iterate without touching code)
  - Use JSON mode for recommendations (structured output via Pydantic validation)
  - Retry once on transient errors, fall back to a safe stub if rate-limited
  - Are wrapped in Streamlit's @st.cache_data in app.py to avoid burning quota
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from groq import Groq, APIError
from dotenv import load_dotenv

from models import FinancialProfile, WellnessScore, RecommendationSet, Recommendation

load_dotenv()

# Groq's current model IDs as of mid-2026. Update via the deprecations page if needed.
MODEL_QUALITY = "llama-3.3-70b-versatile"   # narratives, recommendations
MODEL_FAST = "llama-3.1-8b-instant"         # any quick classification needs

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _client() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError(
            "GROQ_API_KEY not set. Copy .env.example to .env and paste your key from "
            "https://console.groq.com/keys"
        )
    return Groq(api_key=key)


def _profile_context(profile: FinancialProfile, score: WellnessScore) -> str:
    """Render the profile + score as a compact text block for the LLM.

    We hand the LLM the *numbers* the deterministic engine already computed,
    so it doesn't recompute or hallucinate them. Its job is interpretation.
    """
    components_text = "\n".join(
        f"  - {c.name}: {c.score}/{c.max_score} ({c.metric_value:.1f}{c.metric_unit}) — {c.explanation}"
        for c in score.components
    )

    debts_text = "\n".join(
        f"  - {d.name}: ₹{d.outstanding:,.0f} outstanding @ {d.interest_rate}%, EMI ₹{d.monthly_emi:,.0f}"
        for d in profile.debts
    ) or "  (none)"

    return f"""USER PROFILE
Name: {profile.user_name} | Age: {profile.age} | Dependents: {profile.dependents} | City tier: {profile.city_tier}

MONTHLY (INR)
  Income: ₹{profile.income.total:,.0f} (salary ₹{profile.income.monthly_salary:,.0f}, other ₹{profile.income.other_income:,.0f})
  Expenses total: ₹{profile.expenses.total:,.0f}
    Housing: ₹{profile.expenses.housing:,.0f}
    Food: ₹{profile.expenses.food:,.0f}
    Transport: ₹{profile.expenses.transport:,.0f}
    Healthcare: ₹{profile.expenses.healthcare:,.0f}
    Education: ₹{profile.expenses.education:,.0f}
    Entertainment: ₹{profile.expenses.entertainment:,.0f}
    Shopping: ₹{profile.expenses.shopping:,.0f}
    Other: ₹{profile.expenses.other:,.0f}
  Total EMI: ₹{profile.total_emi:,.0f}
  Monthly surplus: ₹{profile.monthly_surplus:,.0f}

DEBTS
{debts_text}

ASSETS (current balances, INR)
  Emergency fund: ₹{profile.savings.emergency_fund:,.0f}
  Fixed deposits (locked): ₹{profile.savings.fixed_deposits:,.0f}
  Investments total: ₹{profile.investments.total:,.0f}
    Equity MFs: ₹{profile.investments.equity_mutual_funds:,.0f}
    Stocks: ₹{profile.investments.stocks:,.0f}
    Debt funds: ₹{profile.investments.debt_funds:,.0f}
    PPF/EPF/NPS: ₹{profile.investments.ppf_epf_nps:,.0f}
    Real estate (excl. primary): ₹{profile.investments.real_estate:,.0f}
    Gold: ₹{profile.investments.gold:,.0f}
    Other: ₹{profile.investments.other:,.0f}

WELLNESS SCORE: {score.total:.0f}/100 (Grade {score.grade})
Component breakdown:
{components_text}
"""


def generate_narrative(profile: FinancialProfile, score: WellnessScore) -> str:
    """Produce a 2-paragraph narrative interpreting the user's spending pattern."""
    system = _load_prompt("narrative.txt")
    user = _profile_context(profile, score)

    try:
        client = _client()
        resp = client.chat.completions.create(
            model=MODEL_QUALITY,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
            max_tokens=600,
        )
        return resp.choices[0].message.content.strip()
    except APIError as e:
        # Fallback: use the deterministic explanations.
        return _fallback_narrative(profile, score, str(e))


def generate_recommendations(
    profile: FinancialProfile, score: WellnessScore
) -> RecommendationSet:
    """Produce exactly 3 prioritised, actionable recommendations as structured JSON."""
    system = _load_prompt("recommendations.txt")
    user = _profile_context(profile, score)

    last_err: Exception | None = None
    for attempt in range(2):
        try:
            client = _client()
            resp = client.chat.completions.create(
                model=MODEL_QUALITY,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content
            data: dict[str, Any] = json.loads(raw)
            return RecommendationSet(**data)
        except (APIError, json.JSONDecodeError, ValueError) as e:
            last_err = e
            time.sleep(1.5 * (attempt + 1))

    # All attempts failed — return a deterministic fallback set.
    return _fallback_recommendations(profile, score, str(last_err))


# ---------- Fallbacks (so the demo never breaks) ----------

def _fallback_narrative(profile: FinancialProfile, score: WellnessScore, err: str) -> str:
    bullets = " ".join(c.explanation for c in score.components)
    return (
        f"Your overall financial wellness score is {score.total:.0f}/100 ({score.grade}). "
        f"{score.headline} {bullets}\n\n"
        f"(Note: AI narrative service unavailable — showing deterministic summary. Error: {err[:80]})"
    )


def _fallback_recommendations(
    profile: FinancialProfile, score: WellnessScore, err: str
) -> RecommendationSet:
    weakest = sorted(score.components, key=lambda c: c.percentage)[:3]
    recs: list[Recommendation] = []
    cat_map = {
        "Savings Rate": "savings",
        "Debt-to-Income": "debt",
        "Emergency Fund": "emergency",
        "Investments": "investment",
        "Discretionary Control": "spending",
    }
    for c in weakest:
        recs.append(
            Recommendation(
                title=f"Improve your {c.name}",
                category=cat_map.get(c.name, "savings"),  # type: ignore[arg-type]
                priority="high",
                expected_impact=f"Raises your overall score toward the {c.max_score:.0f}-point ceiling for this component.",
                action_steps=[
                    f"Review the metric: {c.explanation}",
                    "Set a measurable target for next month.",
                    "Track progress weekly.",
                ],
                rationale=(
                    f"This is one of your lower-scoring areas "
                    f"({c.score:.0f}/{c.max_score:.0f}) and offers the most room to improve."
                ),
            )
        )
    return RecommendationSet(recommendations=recs)
