"""
Benchmarks module — loads from data/benchmarks_derived.json

The JSON file is built by data/build_benchmarks.py using:
  - HCES 2023-24 (MoSPI) for urban spending shares
  - RBI Annual Report 2023-24 for savings/debt thresholds

This module exposes the same public API that score.py and app.py use,
so neither of those files needs to change.
"""

from __future__ import annotations

import json
from pathlib import Path

# ── Load the derived benchmark file ──────────────────────────────────────────

_BENCH_FILE = Path(__file__).parent / "data" / "benchmarks_derived.json"

if not _BENCH_FILE.exists():
    raise FileNotFoundError(
        f"benchmarks_derived.json not found at {_BENCH_FILE}\n"
        "Run: python data/build_benchmarks.py"
    )

with open(_BENCH_FILE, encoding="utf-8") as _f:
    _B = json.load(_f)

# ── Public: spending % of income by city tier ─────────────────────────────────
# Shape: {"tier1": {"food": 27.2, "transport": 7.2, ...}, "tier2": {...}, ...}
# Source: HCES 2023-24, MoSPI, converted from % of MPCE to % of income.

SPENDING_BENCHMARKS_PCT_OF_INCOME: dict[str, dict[str, float]] = (
    _B["spending_pct_of_income"]
)

# ── Public: scoring thresholds ────────────────────────────────────────────────
# Flat dict — same keys score.py already uses.
# Source: RBI FOIR guidelines + SEBI consumer education + HCES-derived.

_T = _B["scoring_thresholds"]

ADVISABLE_THRESHOLDS: dict[str, float | int] = {
    # Savings rate (surplus / income)
    "savings_rate_excellent": _T["savings_rate"]["excellent"],
    "savings_rate_good":      _T["savings_rate"]["good"],
    "savings_rate_okay":      _T["savings_rate"]["okay"],
    "savings_rate_low":       _T["savings_rate"]["low"],

    # Debt-to-income (total EMI / income)
    "dti_excellent": _T["debt_to_income"]["excellent"],
    "dti_good":      _T["debt_to_income"]["good"],
    "dti_okay":      _T["debt_to_income"]["okay"],
    "dti_high":      _T["debt_to_income"]["high"],

    # Emergency fund (months of expenses)
    "emergency_excellent": _T["emergency_fund"]["excellent"],
    "emergency_good":      _T["emergency_fund"]["good"],
    "emergency_okay":      _T["emergency_fund"]["okay"],
    "emergency_low":       _T["emergency_fund"]["low"],

    # Discretionary spending (entertainment + shopping) / income
    "discretionary_excellent": _T["discretionary"]["excellent"],
    "discretionary_good":      _T["discretionary"]["good"],
    "discretionary_okay":      _T["discretionary"]["okay"],
    "discretionary_high":      _T["discretionary"]["high"],
}

# ── Public: Indian household context stats ────────────────────────────────────
# Used by the LLM prompts and report footer for reference statistics.

INDIA_CONTEXT: dict = _B["india_context"]

# ── Public: provenance (for report citations) ─────────────────────────────────

PROVENANCE: dict = _B["provenance"]

# ── Public helper ─────────────────────────────────────────────────────────────

def expected_spending_inr(city_tier: str, monthly_income: float) -> dict[str, float]:
    """
    Return expected monthly spending per category in INR,
    for a given city tier and income level.

    Uses HCES 2023-24 + tier adjustment percentages.
    Falls back to tier1 if an unrecognised tier is passed.
    """
    pcts = SPENDING_BENCHMARKS_PCT_OF_INCOME.get(
        city_tier,
        SPENDING_BENCHMARKS_PCT_OF_INCOME["tier1"],
    )
    return {cat: (pct / 100.0) * monthly_income for cat, pct in pcts.items()}
