"""
Pydantic data models for the Personal Finance Health Report Generator.

Every input from the Streamlit form passes through FinancialProfile.
Every LLM-generated structured output passes through Recommendation.
This is the project's contract — if it doesn't validate here, it doesn't flow.
"""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator


# ---------- Inputs ----------

class IncomeInfo(BaseModel):
    monthly_salary: float = Field(..., ge=0, description="Take-home (post-tax) monthly salary in INR")
    other_income: float = Field(0, ge=0, description="Rental, freelance, dividends, etc.")

    @property
    def total(self) -> float:
        return self.monthly_salary + self.other_income


class Expenses(BaseModel):
    """All values are monthly INR amounts."""
    housing: float = Field(0, ge=0, description="Rent / EMI-housing / utilities / maintenance")
    food: float = Field(0, ge=0, description="Groceries + dining out")
    transport: float = Field(0, ge=0, description="Fuel + cabs + public transport")
    healthcare: float = Field(0, ge=0, description="Insurance premiums + OOP medical")
    education: float = Field(0, ge=0)
    entertainment: float = Field(0, ge=0, description="Subscriptions + outings")
    shopping: float = Field(0, ge=0, description="Clothing + gadgets + non-essentials")
    other: float = Field(0, ge=0)

    @property
    def total(self) -> float:
        return sum(self.model_dump().values())

    @property
    def discretionary(self) -> float:
        """Entertainment + Shopping. Used for the spending-control score."""
        return self.entertainment + self.shopping


class Debt(BaseModel):
    name: str
    outstanding: float = Field(..., ge=0, description="Remaining principal")
    monthly_emi: float = Field(..., ge=0)
    interest_rate: float = Field(..., ge=0, le=100, description="Annual rate, e.g. 8.5 for 8.5%")


class Savings(BaseModel):
    emergency_fund: float = Field(0, ge=0, description="Liquid: SB account + FD that's truly liquid")
    fixed_deposits: float = Field(0, ge=0, description="Locked FDs/RDs (not for emergencies)")


class Investments(BaseModel):
    equity_mutual_funds: float = Field(0, ge=0)
    stocks: float = Field(0, ge=0)
    debt_funds: float = Field(0, ge=0)
    ppf_epf_nps: float = Field(0, ge=0, description="Retirement: PPF + EPF + NPS")
    real_estate: float = Field(0, ge=0, description="Excluding primary residence")
    gold: float = Field(0, ge=0, description="Physical + digital + SGB")
    other: float = Field(0, ge=0)

    @property
    def total(self) -> float:
        return sum(self.model_dump().values())

    @property
    def growth_assets(self) -> float:
        """Assets with equity-like risk/return profile."""
        return self.equity_mutual_funds + self.stocks + self.real_estate

    @property
    def diversification_count(self) -> int:
        """Number of non-zero investment categories."""
        return sum(1 for v in self.model_dump().values() if v > 0)


class FinancialProfile(BaseModel):
    user_name: str = Field(..., min_length=1)
    age: int = Field(..., ge=18, le=100)
    dependents: int = Field(0, ge=0, le=20)
    city_tier: Literal["tier1", "tier2", "tier3"] = "tier1"
    income: IncomeInfo
    expenses: Expenses
    debts: list[Debt] = Field(default_factory=list)
    savings: Savings
    investments: Investments

    @field_validator("debts")
    @classmethod
    def cap_debt_count(cls, v: list[Debt]) -> list[Debt]:
        if len(v) > 10:
            raise ValueError("Maximum 10 debts. If you have more, consolidate first.")
        return v

    @property
    def total_emi(self) -> float:
        return sum(d.monthly_emi for d in self.debts)

    @property
    def total_debt(self) -> float:
        return sum(d.outstanding for d in self.debts)

    @property
    def monthly_surplus(self) -> float:
        return self.income.total - self.expenses.total - self.total_emi

    @property
    def annual_income(self) -> float:
        return self.income.total * 12


# ---------- Outputs ----------

class ComponentScore(BaseModel):
    """One of the 5 score components."""
    name: str
    score: float = Field(..., ge=0)
    max_score: float = Field(..., gt=0)
    metric_value: float
    metric_unit: str = ""
    explanation: str

    @property
    def percentage(self) -> float:
        return (self.score / self.max_score) * 100


class WellnessScore(BaseModel):
    total: float = Field(..., ge=0, le=100)
    components: list[ComponentScore]
    grade: str  # A+ / A / B / C / D
    headline: str  # one-line summary

    @classmethod
    def from_components(cls, components: list[ComponentScore]) -> "WellnessScore":
        total = sum(c.score for c in components)
        grade, headline = _grade_from_total(total)
        return cls(total=total, components=components, grade=grade, headline=headline)


def _grade_from_total(total: float) -> tuple[str, str]:
    if total >= 85:
        return "A+", "Excellent — your financial health is in great shape."
    if total >= 70:
        return "A", "Strong — a few small adjustments will push you to excellent."
    if total >= 55:
        return "B", "Decent foundation, but there are clear gaps to address."
    if total >= 40:
        return "C", "Below average — meaningful changes needed across several areas."
    return "D", "Critical — prioritise stabilising your finances immediately."


class Recommendation(BaseModel):
    """One actionable recommendation. The LLM produces 3 of these per report."""
    title: str = Field(..., min_length=3, max_length=80)
    category: Literal["savings", "debt", "investment", "spending", "insurance", "emergency"]
    priority: Literal["high", "medium", "low"]
    expected_impact: str = Field(..., description="What changes if the user follows this")
    action_steps: list[str] = Field(..., min_length=2, max_length=5)
    rationale: str = Field(..., description="Why this is the right move given the user's numbers")


class RecommendationSet(BaseModel):
    """The 3 prioritised recommendations the LLM returns."""
    recommendations: list[Recommendation] = Field(..., min_length=3, max_length=3)
