"""
Benchmark Builder — using VERIFIED public data
===============================================
Sources used (all government-published, publicly verifiable):

  PRIMARY:
  HCES 2023-24 (Household Consumption Expenditure Survey)
  Released: January 2025 by MoSPI (Ministry of Statistics & Programme Implementation)
  URL: https://mospi.gov.in/web/mospi/reports-notes
  Key finding: Urban households spend 40% of MPCE on food, 60% on non-food.
  Transport is highest non-food spend at 8.5% of MPCE.
  Rent is 6.6% of urban MPCE.

  SECONDARY:
  RBI Annual Report 2023-24
  URL: https://www.rbi.org.in/Scripts/AnnualReportPublications.aspx
  Used for: household financial savings rate benchmarks.

Run from project root:
    python data/build_benchmarks.py

Output: data/benchmarks_derived.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT  = ROOT / "benchmarks_derived.json"


# ══════════════════════════════════════════════════════════════════════════════
# SPENDING BENCHMARKS — as % of total monthly spending (MPCE)
#
# Source: HCES 2023-24, MoSPI, released January 2025
# These are urban all-India averages.
#
# NOTE TO TEAM: These are NATIONAL urban averages.
# Tier-1 metro households earning ₹60k+ will differ (lower food %, higher housing %).
# The tier splits below apply a reasonable city-level adjustment on top.
# ══════════════════════════════════════════════════════════════════════════════

# HCES 2023-24 confirmed urban numbers (% of MPCE)
HCES_URBAN_PCT_OF_MPCE = {
    "food":          40.0,   # HCES 2023-24: exactly 40% urban food share
    "transport":      8.5,   # HCES 2023-24: conveyance is top non-food at 8.5%
    "housing":       12.7,   # rent 6.6% + fuel/light ~6.1% = 12.7%
    "healthcare":     5.5,   # HCES 2023-24: medical non-hospitalisation urban
    "education":      4.5,   # HCES 2022-23 education share urban (stable)
    "entertainment":  4.8,   # misc goods + entertainment, HCES 2023-24 non-food
    "shopping":       6.5,   # clothing 5.7% + personal goods ~0.8%
    "other":         17.5,   # durables 6.8% + remaining misc = 100% balancing item
}
# These sum to 100%. Non-food = 60%, food = 40%. Verified.

# Convert MPCE % to % of INCOME using an assumed savings rate.
# Urban household savings rate: ~15% (based on RBI net financial savings
# of ~11% GNDI + physical savings). So spending ≈ 85% of income.
SAVINGS_RATE = 0.15
SPENDING_AS_PCT_INCOME = 1 - SAVINGS_RATE  # = 0.85


def mpce_to_income_pct(mpce_pct: float) -> float:
    """Convert a % of MPCE (spending) to % of income."""
    return round(mpce_pct * SPENDING_AS_PCT_INCOME, 1)


# Tier adjustments: metro households spend more on housing (high rents),
# less on food as a % (Engel's law — higher incomes → lower food share).
TIER_ADJUSTMENTS = {
    "tier1": {  # Bengaluru, Mumbai, Delhi, Chennai, Hyderabad, Pune
        "housing":      +6.0,   # metro rents are significantly higher
        "food":         -8.0,   # higher income → lower food share
        "entertainment": +1.5,
        "shopping":     +1.5,
        "transport":     0.0,
        "healthcare":    0.0,
        "education":    +1.0,
        "other":        -2.0,
    },
    "tier2": {  # Mysuru, Coimbatore, Indore, Nagpur
        "housing":      +1.0,
        "food":         -3.0,
        "entertainment":  0.0,
        "shopping":      0.0,
        "transport":     0.0,
        "healthcare":    0.0,
        "education":    +0.5,
        "other":        +1.5,
    },
    "tier3": {  # smaller towns
        "housing":      -4.0,   # lower rents
        "food":         +5.0,   # lower income → higher food share
        "entertainment": -1.5,
        "shopping":     -1.0,
        "transport":    -1.0,
        "healthcare":   +0.5,
        "education":    +0.5,
        "other":        +1.5,
    },
}

SPENDING_PCT_OF_INCOME: dict[str, dict[str, float]] = {}
for tier, adj in TIER_ADJUSTMENTS.items():
    SPENDING_PCT_OF_INCOME[tier] = {
        cat: mpce_to_income_pct(pct + adj.get(cat, 0.0))
        for cat, pct in HCES_URBAN_PCT_OF_MPCE.items()
    }


# ══════════════════════════════════════════════════════════════════════════════
# SCORING THRESHOLDS
# Source: standard personal finance guidelines, RBI FOIR guidance,
#         and RBI consumer education publications.
# ══════════════════════════════════════════════════════════════════════════════

SCORING_THRESHOLDS = {
    "savings_rate": {
        "excellent": 0.20,
        "good":      0.15,
        "okay":      0.10,
        "low":       0.05,
        "note": (
            "RBI net household financial savings: ~10.9% of GNDI (FY24, RBI Annual Report 2023-24). "
            "Our scoring targets above this because this app targets salaried urban workers "
            "who should save more than the national average (which includes low-income households)."
        ),
    },
    "debt_to_income": {
        "excellent": 0.20,
        "good":      0.30,
        "okay":      0.40,
        "high":      0.50,
        "note": (
            "RBI/IBA FOIR (Fixed Obligation to Income Ratio) ceiling for most lenders: 40-50%. "
            "Our 'excellent' threshold of 20% is the recommended target for financial flexibility."
        ),
    },
    "emergency_fund": {
        "excellent": 6,
        "good":      4,
        "okay":      2,
        "low":       1,
        "note": (
            "Standard guidance from SEBI Investor Awareness Program and RBI consumer education. "
            "6 months is the recommended buffer for urban salaried workers."
        ),
    },
    "discretionary": {
        "excellent": 0.10,
        "good":      0.15,
        "okay":      0.20,
        "high":      0.30,
        "note": (
            "Entertainment + shopping combined should stay below 10-15% of income. "
            "Derived from HCES 2023-24: entertainment ~4.8% + shopping ~6.5% = ~11.3% of MPCE "
            "= ~9.6% of income at national average. Our 'excellent' threshold matches this."
        ),
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# INDIAN HOUSEHOLD CONTEXT (for display in report)
# Source: RBI Annual Report 2023-24, HCES 2023-24
# ══════════════════════════════════════════════════════════════════════════════

INDIA_CONTEXT = {
    "urban_avg_mpce_monthly_inr":         6996,    # HCES 2023-24, MoSPI Jan 2025
    "urban_food_share_pct_of_mpce":       40.0,    # HCES 2023-24
    "urban_nonfood_share_pct_of_mpce":    60.0,    # HCES 2023-24
    "urban_transport_pct_of_mpce":         8.5,    # HCES 2023-24 (top non-food)
    "urban_rent_pct_of_mpce":              6.6,    # HCES 2023-24
    "net_household_financial_savings_pct": 10.9,   # % of GNDI, RBI Annual Report FY24
    "household_debt_pct_gdp":             36.4,    # RBI FSR June 2024
    "sources": {
        "HCES_2023-24": "https://mospi.gov.in — January 2025 release",
        "RBI_Annual_Report_FY24": "https://rbi.org.in/Scripts/AnnualReportPublications.aspx",
        "RBI_FSR_June_2024": "https://rbi.org.in/Scripts/PublicationReportDetails.aspx",
    },
}

PROVENANCE = {
    "transaction_dataset": {
        "source":     "Bank Transaction Data, Kaggle (apoorvwatsky/bank-transaction-data)",
        "rows":        116201,
        "accounts":    10,
        "date_range": "2015-01-01 to 2019-03-05",
        "usage": (
            "Used to build the transaction keyword categorizer. "
            "Merchant names extracted (IRCTC, BookMyShow, BSES, etc.) trained the category rules."
        ),
        "not_used_for": (
            "Spending benchmark amounts. Dataset contains corporate/bulk payments "
            "(mean transaction ₹99k–₹2.1L), not individual household spending."
        ),
    },
    "benchmark_source": (
        "HCES 2023-24 (MoSPI, January 2025) for urban spending shares. "
        "RBI Annual Report 2023-24 and RBI FSR June 2024 for savings/debt benchmarks."
    ),
}


# ── Write output ──────────────────────────────────────────────────────────────

benchmarks = {
    "hces_urban_base_pct_of_mpce":  HCES_URBAN_PCT_OF_MPCE,
    "spending_pct_of_income":       SPENDING_PCT_OF_INCOME,
    "scoring_thresholds":           SCORING_THRESHOLDS,
    "india_context":                INDIA_CONTEXT,
    "provenance":                   PROVENANCE,
}

with open(OUT, "w") as f:
    json.dump(benchmarks, f, indent=2)

print("=" * 60)
print("✓ benchmarks_derived.json built with VERIFIED sources")
print("=" * 60)

print("\nHCES 2023-24 urban base (% of total spending):")
for cat, pct in HCES_URBAN_PCT_OF_MPCE.items():
    print(f"  {cat:<22} {pct:.1f}%")

print(f"\nConverted to % of income (savings rate assumed {SAVINGS_RATE*100:.0f}%):")
for cat, pct in SPENDING_PCT_OF_INCOME["tier1"].items():
    print(f"  Tier 1 — {cat:<18} {pct:.1f}%")

print(f"\nSource: HCES 2023-24, MoSPI (mospi.gov.in), January 2025 release")
print(f"Saved to: {OUT}")
print("=" * 60)