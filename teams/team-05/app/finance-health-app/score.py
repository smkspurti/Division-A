"""
Financial Wellness Score engine.

Pure functions. No I/O, no Streamlit, no LLM. This module is fully unit-testable
and is the deterministic ground truth — the LLM never overrides what this says.

Score breakdown (max 100):
    Savings Rate                       25
    Debt-to-Income                     25
    Emergency Fund Months              20
    Investment Volume + Diversity      15
    Discretionary Spending Control     15
"""

from __future__ import annotations

from models import (
    FinancialProfile,
    ComponentScore,
    WellnessScore,
)
from benchmarks import ADVISABLE_THRESHOLDS as T


def _piecewise(value: float, ranges: list[tuple[float, float]]) -> float:
    """Pick the first score whose threshold is met. ranges = [(threshold, score), ...]
    sorted by threshold descending for 'higher is better' metrics.
    For 'lower is better', invert: pass (-value, [(-threshold, score), ...])."""
    for threshold, score in ranges:
        if value >= threshold:
            return score
    return ranges[-1][1]  # default: lowest tier


def score_savings_rate(profile: FinancialProfile) -> ComponentScore:
    income = profile.income.total
    if income <= 0:
        return ComponentScore(
            name="Savings Rate", score=0, max_score=25,
            metric_value=0, metric_unit="%",
            explanation="No income recorded — cannot compute savings rate.",
        )

    surplus = profile.monthly_surplus
    rate = surplus / income

    score = _piecewise(rate, [
        (T["savings_rate_excellent"], 25),
        (T["savings_rate_good"], 20),
        (T["savings_rate_okay"], 15),
        (T["savings_rate_low"], 10),
        (0.0, 5),
        (-9e9, 0),
    ])

    if rate >= T["savings_rate_excellent"]:
        explain = f"You save {rate*100:.1f}% of income — well above the 20% target."
    elif rate >= 0:
        explain = f"You save {rate*100:.1f}% of income. Target is 20%+ for strong financial health."
    else:
        explain = f"You're spending {-rate*100:.1f}% more than you earn each month — this is the most urgent thing to fix."

    return ComponentScore(
        name="Savings Rate", score=score, max_score=25,
        metric_value=rate * 100, metric_unit="%", explanation=explain,
    )


def score_debt_to_income(profile: FinancialProfile) -> ComponentScore:
    income = profile.income.total
    if income <= 0:
        return ComponentScore(
            name="Debt-to-Income", score=0, max_score=25,
            metric_value=0, metric_unit="%",
            explanation="No income recorded — cannot compute debt-to-income.",
        )

    dti = profile.total_emi / income

    # Lower is better — invert sign trick.
    score = _piecewise(-dti, [
        (-T["dti_excellent"], 25),
        (-T["dti_good"], 20),
        (-T["dti_okay"], 15),
        (-T["dti_high"], 8),
        (-9e9, 0),
    ])

    if profile.total_emi == 0:
        explain = "You have no monthly EMIs — full marks on debt burden."
    elif dti <= T["dti_excellent"]:
        explain = f"Your EMIs are {dti*100:.1f}% of income, comfortably below the 20% recommended ceiling."
    elif dti <= T["dti_okay"]:
        explain = f"EMIs at {dti*100:.1f}% of income — manageable, but leaves limited room for new commitments."
    else:
        explain = f"EMIs consume {dti*100:.1f}% of income. Banks typically lend up to 50% — you're stretched."

    return ComponentScore(
        name="Debt-to-Income", score=score, max_score=25,
        metric_value=dti * 100, metric_unit="%", explanation=explain,
    )


def score_emergency_fund(profile: FinancialProfile) -> ComponentScore:
    monthly_expenses = profile.expenses.total + profile.total_emi
    if monthly_expenses <= 0:
        # Edge case: no expenses recorded. Treat liquid savings vs income.
        monthly_expenses = profile.income.total or 1

    months_covered = profile.savings.emergency_fund / monthly_expenses

    score = _piecewise(months_covered, [
        (T["emergency_excellent"], 20),
        (T["emergency_good"], 15),
        (T["emergency_okay"], 10),
        (T["emergency_low"], 5),
        (0, 0),
    ])

    if months_covered >= 6:
        explain = f"Your emergency fund covers {months_covered:.1f} months of expenses — strong cushion."
    elif months_covered >= 1:
        explain = f"Your emergency fund covers {months_covered:.1f} months. Target is 6 months."
    else:
        explain = "You have less than one month of expenses in liquid savings — first priority to fix."

    return ComponentScore(
        name="Emergency Fund", score=score, max_score=20,
        metric_value=months_covered, metric_unit="months", explanation=explain,
    )


def score_investments(profile: FinancialProfile) -> ComponentScore:
    """
    Two-part: 10 pts on investment-to-annual-income ratio, 5 pts on diversification.
    """
    annual = profile.annual_income or 1
    inv_ratio = profile.investments.total / annual

    # Age-adjusted target: by age 30, ~1x annual income invested is healthy.
    # By 40, 3x. By 50, 6x. So target = max(0.3, (age - 22) * 0.15).
    target = max(0.3, (profile.age - 22) * 0.15)
    progress = min(inv_ratio / target, 1.0) if target > 0 else 0

    volume_score = round(progress * 10, 1)
    diversification_score = min(profile.investments.diversification_count, 5)

    total_score = volume_score + diversification_score

    if total_score >= 13:
        explain = f"You hold {inv_ratio:.1f}x annual income in investments across {profile.investments.diversification_count} categories — well-diversified portfolio."
    elif total_score >= 8:
        explain = f"You hold {inv_ratio:.1f}x annual income in investments. Building, but room to grow."
    elif profile.investments.total > 0:
        explain = f"Investments are {inv_ratio:.1f}x annual income — early stage. Consistency matters more than amount."
    else:
        explain = "No investments recorded. Even a small SIP started now compounds significantly."

    return ComponentScore(
        name="Investments", score=total_score, max_score=15,
        metric_value=inv_ratio, metric_unit="x annual income", explanation=explain,
    )


def score_discretionary_control(profile: FinancialProfile) -> ComponentScore:
    income = profile.income.total
    if income <= 0:
        return ComponentScore(
            name="Discretionary Control", score=0, max_score=15,
            metric_value=0, metric_unit="%",
            explanation="No income recorded — cannot compute discretionary ratio.",
        )

    disc = profile.expenses.discretionary
    ratio = disc / income

    score = _piecewise(-ratio, [
        (-T["discretionary_excellent"], 15),
        (-T["discretionary_good"], 12),
        (-T["discretionary_okay"], 8),
        (-T["discretionary_high"], 4),
        (-9e9, 0),
    ])

    if ratio <= T["discretionary_excellent"]:
        explain = f"You spend {ratio*100:.1f}% of income on entertainment + shopping — tightly controlled."
    elif ratio <= T["discretionary_okay"]:
        explain = f"Discretionary spending is {ratio*100:.1f}% of income — reasonable but watch for lifestyle creep."
    else:
        explain = f"Discretionary spending at {ratio*100:.1f}% of income is high — main lever for raising your savings rate."

    return ComponentScore(
        name="Discretionary Control", score=score, max_score=15,
        metric_value=ratio * 100, metric_unit="%", explanation=explain,
    )


def compute_wellness_score(profile: FinancialProfile) -> WellnessScore:
    """The single public entrypoint. Run all five components and assemble."""
    components = [
        score_savings_rate(profile),
        score_debt_to_income(profile),
        score_emergency_fund(profile),
        score_investments(profile),
        score_discretionary_control(profile),
    ]
    return WellnessScore.from_components(components)
