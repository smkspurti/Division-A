import pandas as pd
from preprocess import get_best_mandi

def find_best_mandi(df, crop, farmer_district=None):
    mandi_df = get_best_mandi(df, crop)

    if mandi_df is None or mandi_df.empty:
        return None, None, None, None

    # ── If farmer's district known, prefer local mandis ────────
    if farmer_district:
        local = mandi_df[mandi_df['District'].str.lower() == farmer_district.lower()]
        if not local.empty:
            best_row = local.iloc[0]
            return (
                best_row['Market'],
                best_row['District'],
                best_row['Avg_Price'],
                mandi_df   # still return full table for display
            )

    # Else return the statewide best
    best_row = mandi_df.iloc[0]
    return (
        best_row['Market'],
        best_row['District'],
        best_row['Avg_Price'],
        mandi_df
    )
