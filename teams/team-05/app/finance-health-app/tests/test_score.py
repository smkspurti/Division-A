"""
Unit tests for the financial scoring engine.

Run with: pytest -q

These tests assert *behavior*, not exact numbers, so the team can tune
thresholds in benchmarks.py without breaking the suite.
"""

from __future__ import annotations

import pytest

from models import (
    FinancialProfile, IncomeInfo, Expenses, Debt, Savings, Investments,
)
from score import (
    compute_wellness_score,
    score_savings_rate,
    score_debt_to_income,
    score_emergency_fund,
)


def _profile(**overrides) -> FinancialProfile:
    """Build a profile with reasonable defaults; override fields per test."""
    defaults = dict(
        user_name="Test User", age=30, dependents=0, city_tier="tier1",
        income=IncomeInfo(monthly_salary=100000, other_income=0),
        expenses=Expenses(housing=25000, food=12000, transport=5000,
                          healthcare=2000, education=0, entertainment=4000,
                          shopping=5000, other=2000),
        debts=[],
        savings=Savings(emergency_fund=300000, fixed_deposits=0),
        investments=Investments(
            equity_mutual_funds=200000, stocks=50000, debt_funds=0,
            ppf_epf_nps=150000, real_estate=0, gold=20000, other=0,
        ),
    )
    defaults.update(overrides)
    return FinancialProfile(**defaults)


def test_score_total_in_range():
    score = compute_wellness_score(_profile())
    assert 0 <= score.total <= 100


def test_negative_surplus_zeroes_savings_component():
    # Spending > Income → savings rate must score 0.
    p = _profile(
        income=IncomeInfo(monthly_salary=50000, other_income=0),
        expenses=Expenses(housing=30000, food=15000, transport=5000,
                          healthcare=3000, education=0, entertainment=2000,
                          shopping=3000, other=2000),
    )
    assert score_savings_rate(p).score == 0


def test_zero_emi_full_dti_score():
    p = _profile(debts=[])
    s = score_debt_to_income(p)
    assert s.score == s.max_score


def test_high_dti_lowers_score():
    p = _profile(
        income=IncomeInfo(monthly_salary=60000, other_income=0),
        debts=[Debt(name="Home Loan", outstanding=2000000, monthly_emi=35000, interest_rate=8.5)],
    )
    s = score_debt_to_income(p)
    assert s.score < 10


def test_six_month_emergency_fund_full_score():
    # Expenses + EMI = 50000/month → 300000 = 6 months → full marks.
    p = _profile(
        expenses=Expenses(housing=20000, food=10000, transport=4000,
                          healthcare=2000, education=0, entertainment=4000,
                          shopping=8000, other=2000),  # total 50000
        savings=Savings(emergency_fund=300000, fixed_deposits=0),
    )
    s = score_emergency_fund(p)
    assert s.score == s.max_score


def test_no_emergency_fund_zeroes_component():
    p = _profile(savings=Savings(emergency_fund=0, fixed_deposits=500000))
    s = score_emergency_fund(p)
    assert s.score == 0


def test_grade_thresholds():
    score = compute_wellness_score(_profile())
    assert score.grade in {"A+", "A", "B", "C", "D"}
    assert isinstance(score.headline, str) and score.headline


def test_components_sum_to_total():
    score = compute_wellness_score(_profile())
    assert abs(sum(c.score for c in score.components) - score.total) < 0.01


def test_zero_income_doesnt_crash():
    p = _profile(income=IncomeInfo(monthly_salary=0, other_income=0))
    score = compute_wellness_score(p)
    assert score.total >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
