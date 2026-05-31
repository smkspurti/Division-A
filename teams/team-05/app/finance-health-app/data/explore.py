"""
Run this from the project root:
    python data/explore.py

It will find the dataset automatically and print everything we need
to build the category mapping and benchmarks.
"""

import pandas as pd
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

# ── Step 1: Find the data file automatically ──────────────────────────────────

DATA_DIR = Path(__file__).parent / "plaid_synthetic"
SUPPORTED = [".csv", ".xlsx", ".xls"]

files = [f for f in DATA_DIR.rglob("*") if f.suffix.lower() in SUPPORTED]

if not files:
    print("ERROR: No CSV or Excel files found in data/plaid_synthetic/")
    print("Please make sure the download completed. Run: python scripts/download_data.py")
    exit(1)

print(f"Found {len(files)} data file(s):")
for f in files:
    print(f"  {f.name}  ({f.stat().st_size / 1024:.1f} KB)")

# Use the first file found
TARGET = files[0]
print(f"\nReading: {TARGET.name}")

# ── Step 2: Load the file ─────────────────────────────────────────────────────

if TARGET.suffix.lower() == ".csv":
    try:
        df = pd.read_csv(TARGET, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(TARGET, encoding="latin-1")
else:
    # Excel
    xl = pd.ExcelFile(TARGET)
    print(f"  Sheets found: {xl.sheet_names}")
    # Load all sheets and combine
    frames = []
    for sheet in xl.sheet_names:
        tmp = pd.read_excel(TARGET, sheet_name=sheet)
        tmp["_sheet"] = sheet
        frames.append(tmp)
    df = pd.concat(frames, ignore_index=True)

print(f"  Loaded successfully.\n")

# ── Step 3: Basic shape ───────────────────────────────────────────────────────

print("=" * 60)
print("SECTION 1: BASIC INFO")
print("=" * 60)
print(f"Total rows     : {len(df):,}")
print(f"Total columns  : {len(df.columns)}")
print(f"\nColumn names:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. '{col}'")

# ── Step 4: Sample rows ───────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 2: FIRST 5 ROWS")
print("=" * 60)
pd.set_option("display.max_colwidth", 40)
pd.set_option("display.width", 120)
print(df.head(5).to_string())

# ── Step 5: Detect key columns ────────────────────────────────────────────────

print("\n" + "=" * 60)
print("SECTION 3: COLUMN DATA TYPES & NULL COUNTS")
print("=" * 60)
for col in df.columns:
    nulls = df[col].isna().sum()
    dtype = df[col].dtype
    print(f"  {col:<30} dtype={str(dtype):<12} nulls={nulls}")

# ── Step 6: Date range ────────────────────────────────────────────────────────

# Try to find a date column
date_cols = [c for c in df.columns if "date" in c.lower()]
print("\n" + "=" * 60)
print("SECTION 4: DATE RANGE")
print("=" * 60)
if date_cols:
    for dc in date_cols:
        try:
            dates = pd.to_datetime(df[dc], dayfirst=True, errors="coerce")
            valid = dates.dropna()
            if len(valid) > 0:
                print(f"  Column '{dc}': {valid.min().date()} → {valid.max().date()}  ({len(valid):,} valid dates)")
        except Exception as e:
            print(f"  Column '{dc}': could not parse — {e}")
else:
    print("  No date columns found.")

# ── Step 7: Transaction description analysis ──────────────────────────────────

# Find the description/narration column
desc_col_candidates = [
    c for c in df.columns
    if any(k in c.lower() for k in ["detail", "description", "narration", "remark", "transaction", "particular"])
]

print("\n" + "=" * 60)
print("SECTION 5: TRANSACTION DESCRIPTIONS (top 30)")
print("=" * 60)
if desc_col_candidates:
    desc_col = desc_col_candidates[0]
    print(f"  Using column: '{desc_col}'\n")
    top = df[desc_col].dropna().value_counts().head(30)
    for i, (desc, count) in enumerate(top.items(), 1):
        print(f"  {i:>2}. ({count:>5}x)  {str(desc)[:70]}")
else:
    print("  Could not auto-detect description column.")
    print("  All unique values in STRING columns:")
    for col in df.select_dtypes(include="object").columns:
        uniq = df[col].nunique()
        sample = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else "empty"
        print(f"    '{col}' — {uniq} unique values — sample: {str(sample)[:50]}")

# ── Step 8: Amount columns ────────────────────────────────────────────────────

amt_cols = [c for c in df.columns if any(k in c.lower() for k in ["amt", "amount", "debit", "credit", "withdrawal", "deposit"])]

print("\n" + "=" * 60)
print("SECTION 6: AMOUNT COLUMNS (min/max/mean)")
print("=" * 60)
if amt_cols:
    for ac in amt_cols:
        # Strip commas if stored as strings
        try:
            series = df[ac].astype(str).str.replace(",", "").str.strip()
            series = pd.to_numeric(series, errors="coerce").dropna()
            if len(series) > 0:
                print(f"  {ac:<30} min={series.min():>14,.2f}  max={series.max():>14,.2f}  mean={series.mean():>14,.2f}  non-null={len(series):,}")
            else:
                print(f"  {ac:<30} — all null after parsing")
        except Exception as e:
            print(f"  {ac:<30} — parse error: {e}")
else:
    print("  No amount columns detected.")

# ── Step 9: Unique accounts ───────────────────────────────────────────────────

acct_cols = [c for c in df.columns if any(k in c.lower() for k in ["account", "acct", "acc"])]
print("\n" + "=" * 60)
print("SECTION 7: UNIQUE ACCOUNTS")
print("=" * 60)
if acct_cols:
    for ac in acct_cols:
        print(f"  Column '{ac}': {df[ac].nunique():,} unique accounts")
else:
    print("  No account column detected.")

# ── Step 10: First 40 raw description values for keyword mapping ──────────────

print("\n" + "=" * 60)
print("SECTION 8: RAW DESCRIPTION SAMPLES (for keyword mapping)")
print("=" * 60)
if desc_col_candidates:
    samples = df[desc_col_candidates[0]].dropna().unique()[:60]
    for i, s in enumerate(samples, 1):
        print(f"  {i:>2}. {str(s)[:80]}")

print("\n" + "=" * 60)
print("DONE. Copy everything above and send it.")
print("=" * 60)