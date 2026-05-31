"""
Download the bank transaction dataset from Kaggle.

Usage:
    python scripts/download_data.py

Prerequisites:
    1. Create a Kaggle account at https://www.kaggle.com (free, ~30 seconds)
    2. Go to https://www.kaggle.com/settings/account
    3. Scroll to "API" section → click "Create New Token"
       This downloads kaggle.json
    4. Place kaggle.json at:
         Linux/Mac:  ~/.kaggle/kaggle.json
         Windows:    C:\\Users\\<you>\\.kaggle\\kaggle.json
    5. Linux/Mac only: chmod 600 ~/.kaggle/kaggle.json

Then run this script. It will:
    - Verify Kaggle credentials are set up
    - Install the kaggle package if missing
    - Download the dataset to data/plaid_synthetic/
    - Unzip and validate
    - Print a summary of what's inside
"""

from __future__ import annotations

import os
import sys
import subprocess
import zipfile
from pathlib import Path


DATASET = "apoorvwatsky/bank-transaction-data"
OUT_DIR = Path(__file__).parent.parent / "data" / "plaid_synthetic"


def _check_kaggle_credentials() -> bool:
    """Verify kaggle.json is in the right place."""
    candidates = [
        Path.home() / ".kaggle" / "kaggle.json",
        Path(os.environ.get("KAGGLE_CONFIG_DIR", "")) / "kaggle.json" if os.environ.get("KAGGLE_CONFIG_DIR") else None,
    ]
    candidates = [p for p in candidates if p is not None]

    for p in candidates:
        if p.exists():
            print(f"✓ Found Kaggle credentials at {p}")
            # On Linux/Mac, enforce permissions
            if os.name != "nt":
                try:
                    p.chmod(0o600)
                except Exception:
                    pass
            return True

    print("✗ kaggle.json not found.")
    print("\nSetup steps:")
    print("  1. Sign in at https://www.kaggle.com")
    print("  2. Go to https://www.kaggle.com/settings/account")
    print("  3. Scroll to 'API' → click 'Create New Token'")
    print("  4. Save the downloaded kaggle.json to:")
    if os.name == "nt":
        print(f"        {Path.home() / '.kaggle' / 'kaggle.json'}")
    else:
        print(f"        ~/.kaggle/kaggle.json")
        print("     then run: chmod 600 ~/.kaggle/kaggle.json")
    print("  5. Re-run this script.")
    return False


def _ensure_kaggle_installed() -> bool:
    """Pip-install the kaggle package if not present."""
    try:
        import kaggle  # noqa: F401
        print("✓ kaggle package available")
        return True
    except ImportError:
        print("Installing kaggle package...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "kaggle"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"✗ pip install kaggle failed:\n{result.stderr}")
            return False
        print("✓ kaggle installed")
        return True


def _download() -> bool:
    """Download and unzip the dataset."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nDownloading {DATASET} to {OUT_DIR}...")
    result = subprocess.run(
        [sys.executable, "-m", "kaggle", "datasets", "download",
         "-d", DATASET, "-p", str(OUT_DIR), "--unzip"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"✗ Kaggle download failed:")
        print(result.stderr)
        # Check for common issues
        if "403" in result.stderr or "Forbidden" in result.stderr:
            print("  → 403 usually means you haven't accepted the dataset's terms.")
            print(f"  → Visit https://www.kaggle.com/datasets/{DATASET} in your browser,")
            print("    click the dataset, scroll down and click 'Download' once to accept terms,")
            print("    then re-run this script. (The CLI download will then work.)")
        return False
    print("✓ Download complete")
    return True


def _summarise() -> None:
    """Print what we got."""
    files = sorted(OUT_DIR.rglob("*"))
    if not files:
        print("⚠ No files found in output directory.")
        return

    print(f"\nFiles in {OUT_DIR}:")
    for f in files:
        if f.is_file():
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"  {f.relative_to(OUT_DIR)}  ({size_mb:.2f} MB)")

    # Try to preview the first CSV/XLSX we find
    data_files = [f for f in files if f.suffix.lower() in {".csv", ".xlsx", ".xls"}]
    if not data_files:
        print("\n⚠ No CSV/XLSX files found — check the contents manually.")
        return

    target = data_files[0]
    print(f"\nPreviewing {target.name}:")
    try:
        import pandas as pd
        if target.suffix.lower() == ".csv":
            df = pd.read_csv(target, nrows=5)
        else:
            df = pd.read_excel(target, nrows=5)
        print(f"  Shape (first 5 rows): {df.shape}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\n  Sample:")
        print(df.to_string(max_cols=8, max_colwidth=30))
    except Exception as e:
        print(f"  Could not preview: {e}")


def main() -> int:
    print("=" * 60)
    print("Plaid / Bank Transaction Dataset Download")
    print("=" * 60)

    if not _ensure_kaggle_installed():
        return 1
    if not _check_kaggle_credentials():
        return 1
    if not _download():
        return 1

    _summarise()

    print("\n" + "=" * 60)
    print("✓ Dataset ready. Next steps:")
    print("  1. Open notebooks/01_plaid_exploration.ipynb")
    print("  2. Run through it to understand the schema")
    print("  3. Build data/derive_benchmarks.py from there")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
