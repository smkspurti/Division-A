import pandas as pd


def load_karnataka_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)

    # --- Step 1: Standardize column names ---
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Handle common CEDA column name variants
    rename_map = {
        "arrival_date": "date",
        "price_date": "date",
        "modal_price": "modal_price",
        "modal": "modal_price",
        "min_price": "min_price",
        "minimum_price": "min_price",
        "max_price": "max_price",
        "maximum_price": "max_price",
        "state_name": "state",
        "district_name": "district",
        "market_name": "market",
        "commodity_name": "commodity",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)

    # --- Step 2: Filter Karnataka only ---
    if "state" in df.columns:
        df = df[df["state"].str.lower().str.contains("karnataka", na=False)]

    # --- Step 3: Parse dates ---
    df["date"] = pd.to_datetime(df["date"], dayfirst=True, errors="coerce")
    df.dropna(subset=["date"], inplace=True)

    # --- Step 4: Fix price columns ---
    for col in ["modal_price", "min_price", "max_price"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].replace("N/A", float("nan")), errors="coerce")

    # --- Step 5: Drop duplicates ---
    df.drop_duplicates(subset=["date", "commodity", "market"], inplace=True)

    # --- Step 6: Drop rows where modal_price is missing ---
    df.dropna(subset=["modal_price"], inplace=True)

    # --- Step 7: Sort ---
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    print(f"Loaded {len(df)} rows | {df['commodity'].nunique()} commodities | "
          f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")

    return df


def get_commodity_df(df: pd.DataFrame, commodity: str) -> pd.DataFrame:
    """
    Returns daily aggregated modal price for one commodity across all Karnataka mandis.
    Prophet needs columns named 'ds' and 'y'.
    """
    cdf = df[df["commodity"].str.lower() == commodity.lower()].copy()
    cdf = cdf.groupby("date")["modal_price"].mean().reset_index()
    cdf.columns = ["ds", "y"]
    cdf = cdf[cdf["y"] > 0]
    return cdf


if __name__ == "__main__":
    df = load_karnataka_data("data/karnataka_raw.csv")
    print(df[["date", "commodity", "market", "modal_price"]].head(10))
    print("\nTop 10 commodities by row count:")
    print(df["commodity"].value_counts().head(10))
