"""
Transaction Categorizer
=======================
Reads bank.xlsx, categorizes every transaction using keyword rules,
saves the categorized output, and prints a summary.

Run from project root:
    python data/categorize.py

Outputs:
    data/transactions_categorized.csv   -- full dataset with category column
    data/category_summary.json          -- counts and % per category
"""

import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "plaid_synthetic" / "bank.xlsx"
OUT_CSV   = ROOT / "transactions_categorized.csv"
OUT_JSON  = ROOT / "category_summary.json"

# ── Keyword rules ──────────────────────────────────────────────────────────────
# First match wins. Keep "transfer" and "income" first so internals are
# filtered out before we try to assign a spending category.

CATEGORY_RULES: dict[str, list[str]] = {

    # Internal / non-spending (excluded from household benchmarks)
    "transfer": [
        "internal fund", "fund transfe", "neft", "rtgs", "imps",
        "trf to", "trf from", "trf frm", "sweep trf", "fdrl",
        "indo gibl", "indiaforensic", "fund transfer",
        "synergistic financial", "sonata finance", "nomisma",
        "pasfar", "commdel", "bidderboy", "zaak epay",
        "oxygen nfs", "aeps acquiring",
    ],
    "income": [
        "cashdep", "cash dep", "salary", "wage", "credit by",
        "refund", "cashback", "reversal",
    ],

    # ── Spending categories ────────────────────────────────────────────────────
    "housing": [
        "rent", "house rent", "maintenance", "society", "apartment",
        # Electricity boards — VERY common in Indian bank statements
        "bescom", "tpddl", "msedcl", "tneb", "bses rajdhani", "bses yamuna",
        "north delhi power", "tata power", "adani electricity",
        "cesc", "torrent power", "jbvnl", "pspcl",
        # Gas / utilities
        "gas bill", "mahanagar gas", "indraprastha gas", "gujarat gas",
        "broadband", "airtel", "jio", "bsnl",
        "electricity", "water bill", "fuel light",
        "billpay",  # catch "BILLPAY TATA POWER" etc.
    ],
    "food": [
        "swiggy", "zomato", "dominos", "domino", "mcdonalds", "mcdonald",
        "kfc", "pizza", "burger", "subway", "restaurant", "cafe", "canteen",
        "bigbasket", "big basket", "grofers", "blinkit", "dunzo",
        "natures basket", "reliance fresh", "more supermarket",
        "food", "grocery", "supermarket", "bakery", "haldiram",
        "milk", "dairy",
    ],
    "transport": [
        "irctc", "indian railway", "railways", "uber", "ola cab",
        "rapido", "metro", "petrol", "fuel", "diesel",
        "makemytrip", "yatra", "goibibo", "redbus", "easemytrip",
        "indigo", "spicejet", "air india", "vistara",
        "parking", "fastag", "toll", "cab service",
    ],
    "entertainment": [
        "bigtree", "bookmyshow", "book my show", "netflix", "amazon prime",
        "hotstar", "disney", "spotify", "pvr", "inox", "cinepolis",
        "cinema", "theatre", "mehar entertainment", "avenues india",
        "gaming", "playstation", "steam",
        "dish infra", "dishtv", "tata sky", "sun direct", "d2h",  # DTH
        "e-billing solution",   # EBSL — often entertainment billing
    ],
    "shopping": [
        "amazon", "flipkart", "myntra", "ajio", "nykaa", "meesho",
        "snapdeal", "reliance retail", "big bazaar", "dmart", "d-mart",
        "lifestyle", "westside", "shoppers", "max fashion",
        "future retail",        # Big Bazaar / Ezone parent
        "localcube",            # B2C commerce
        "qwikcilver",           # Gift cards / shopping vouchers
        "payu payments", "indiaideas", "billdesk",  # Payment gateways (shopping)
        "avenues india",
    ],
    "healthcare": [
        "apollo", "medplus", "netmeds", "1mg", "pharmeasy",
        "pharma", "pharmacy", "hospital", "clinic", "doctor",
        "health", "medical", "medicine", "diagnostic", "lab",
        "manipal", "fortis", "aiims", "narayana",
    ],
    "education": [
        "byju", "unacademy", "vedantu", "toppr", "coursera",
        "udemy", "upgrad", "school fee", "college fee", "tuition",
        "coaching", "university", "institute",
    ],
}


def categorize(description: str) -> str:
    if pd.isna(description):
        return "other"
    desc = str(description).lower().strip()
    for category, keywords in CATEGORY_RULES.items():
        for kw in keywords:
            if kw in desc:
                return category
    return "other"


# ── Load ───────────────────────────────────────────────────────────────────────
print("Loading bank.xlsx...")
xl = pd.ExcelFile(DATA_FILE)
frames = [pd.read_excel(DATA_FILE, sheet_name=s) for s in xl.sheet_names]
df = pd.concat(frames, ignore_index=True)
print(f"  Loaded {len(df):,} rows\n")

df["CATEGORY"] = df["TRANSACTION DETAILS"].apply(categorize)

for col in ["WITHDRAWAL AMT", "DEPOSIT AMT"]:
    df[col] = (
        df[col].astype(str).str.replace(",", "")
        .pipe(pd.to_numeric, errors="coerce")
    )

# ── Category distribution ──────────────────────────────────────────────────────
print("=" * 60)
print("CATEGORY DISTRIBUTION (all 116k rows)")
print("=" * 60)
counts = df["CATEGORY"].value_counts()
for cat, cnt in counts.items():
    print(f"  {cat:<22} {cnt:>7,}  ({cnt/len(df)*100:>5.1f}%)")

# ── Spending breakdown ─────────────────────────────────────────────────────────
SPEND_CATS = ["food","transport","entertainment","shopping","healthcare","education","housing"]
spend = df[df["CATEGORY"].isin(SPEND_CATS) & df["WITHDRAWAL AMT"].notna()].copy()

print(f"\n{'='*60}")
print(f"SPENDING ROWS: {len(spend):,} of {len(df):,} ({len(spend)/len(df)*100:.1f}%)")
print("=" * 60)
total = spend["WITHDRAWAL AMT"].sum()
grp = spend.groupby("CATEGORY")["WITHDRAWAL AMT"].agg(["sum","count","mean"]).sort_values("sum", ascending=False)
for cat in grp.index:
    pct  = grp.loc[cat,"sum"] / total * 100
    cnt  = int(grp.loc[cat,"count"])
    mean = grp.loc[cat,"mean"]
    print(f"  {cat:<22} {pct:>5.1f}% of spend  {cnt:>5,} txns  mean ₹{mean:>10,.0f}")

# ── Still uncategorized ────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("STILL UNCATEGORIZED (top 20) — for further rule improvement")
print("=" * 60)
other_top = (
    df[df["CATEGORY"] == "other"]["TRANSACTION DETAILS"]
    .dropna().value_counts().head(20)
)
for desc, cnt in other_top.items():
    print(f"  ({cnt:>5}x)  {str(desc)[:70]}")

# ── Save ───────────────────────────────────────────────────────────────────────
df.to_csv(OUT_CSV, index=False)
summary = {}
for cat in grp.index:
    summary[cat] = {
        "pct_of_spend": round(grp.loc[cat,"sum"]/total*100, 2),
        "txn_count": int(grp.loc[cat,"count"]),
        "mean_txn_amount": round(grp.loc[cat,"mean"], 2),
    }
with open(OUT_JSON, "w") as f:
    json.dump(summary, f, indent=2)

print(f"\n✓ Saved → {OUT_CSV}")
print(f"✓ Saved → {OUT_JSON}")
print(f"\n{'='*60}\nDONE. Copy full output and send it.\n{'='*60}")