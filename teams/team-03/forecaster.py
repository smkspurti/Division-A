import pandas as pd
import json
from datetime import date, timedelta
from prophet import Prophet
from data_loader import load_karnataka_data, get_commodity_df

# ── Detect data frequency ─────────────────────────────────────
def detect_freq(cdf: pd.DataFrame) -> str:
    """Returns 'MS' if monthly data, 'D' if daily."""
    gaps = cdf["ds"].sort_values().diff().dt.days.dropna()
    return "MS" if gaps.median() >= 20 else "D"


# ── Indian agricultural holidays (2023–2026) ──────────────────
INDIAN_HOLIDAYS = pd.DataFrame({
    "holiday": "india_agri_holiday",
    "ds": pd.to_datetime([
        # Sankranti / Pongal — harvest festival
        "2023-01-14", "2024-01-14", "2025-01-14", "2026-01-14",
        # Holi
        "2023-03-08", "2024-03-25", "2025-03-14", "2026-03-03",
        # Ugadi — Karnataka new year
        "2023-04-14", "2024-04-09", "2025-03-30", "2026-03-19",
        # Dussehra
        "2023-10-24", "2024-10-12", "2025-10-02", "2026-10-20",
        # Diwali
        "2023-11-13", "2024-11-01", "2025-10-20", "2026-11-08",
        # Kharif harvest (Oct) — major price movement
        "2023-10-01", "2024-10-01", "2025-10-01", "2026-10-01",
        # Rabi harvest (Apr)
        "2023-04-01", "2024-04-01", "2025-04-01", "2026-04-01",
    ]),
    "lower_window": -2,
    "upper_window": 2,
})


# ── Core forecast function ────────────────────────────────────
def forecast_commodity(
    cdf: pd.DataFrame,
    commodity: str,
    forecast_days: int = 7,
    start_date: date = None,
) -> tuple:
    """
    Trains Prophet on historical prices and returns a forecast
    starting from start_date (bridges the gap from last training data).

    Parameters
    ----------
    cdf          : DataFrame with 'ds' (datetime) and 'y' (price)
    commodity    : commodity name string
    forecast_days: number of periods to show in output window
    start_date   : date farmer wants forecast from (can be far future)

    Returns
    -------
    result       : dict with forecast metadata and rows
    forecast_df  : full Prophet forecast DataFrame
    model        : fitted Prophet model
    """
    if len(cdf) < 30:
        err = {"error": f"Not enough data for {commodity} (only {len(cdf)} rows)"}
        return err, None, None

    freq       = detect_freq(cdf)
    is_monthly = (freq == "MS")

    # Price cap/floor — prevents negative prices and wild extrapolation
    price_cap   = cdf["y"].max() * 2.5
    price_floor = 0.0

    cdf = cdf.copy()
    cdf["cap"]   = price_cap
    cdf["floor"] = price_floor

    # ── Model ─────────────────────────────────────────────────
    model = Prophet(
        growth="logistic",               # respects floor and cap
        changepoint_prior_scale=0.05,    # conservative — avoids wild trend extrapolation
        seasonality_prior_scale=10,
        holidays=INDIAN_HOLIDAYS,
        yearly_seasonality=True,
        weekly_seasonality=not is_monthly,  # no weekly signal in monthly data
        daily_seasonality=False,
        interval_width=0.80,
    )

    if not is_monthly:
        model.add_seasonality(name="monthly", period=30.5, fourier_order=5)

    model.fit(cdf)

    # ── Bridge gap from last data date to start_date ──────────
    last_data_date = cdf["ds"].max().normalize()

    if start_date is None:
        start_date = (last_data_date + timedelta(days=1)).date()

    start_ts = pd.Timestamp(start_date)

    if is_monthly:
        months_to_start = max(
            0,
            (start_ts.year - last_data_date.year) * 12
            + (start_ts.month - last_data_date.month)
        )
        total_periods = months_to_start + forecast_days
    else:
        days_to_start = max(0, (start_ts - last_data_date).days)
        total_periods = days_to_start + forecast_days

    total_periods = max(total_periods, forecast_days)

    # ── Future dataframe ──────────────────────────────────────
    future = model.make_future_dataframe(periods=total_periods, freq=freq)
    future["cap"]   = price_cap
    future["floor"] = price_floor

    forecast = model.predict(future)

    # ── Slice only the requested window ───────────────────────
    forecast["ds"] = pd.to_datetime(forecast["ds"])
    forecast_window = (
        forecast[forecast["ds"] >= start_ts]
        .head(forecast_days)[["ds", "yhat", "yhat_lower", "yhat_upper"]]
        .copy()
    )

    # Clamp to floor/cap explicitly
    for col in ["yhat", "yhat_lower", "yhat_upper"]:
        forecast_window[col] = forecast_window[col].clip(lower=price_floor, upper=price_cap)

    # ── Result dict ───────────────────────────────────────────
    result = {
        "commodity": commodity,
        "data_frequency": freq,
        "forecast_days": forecast_days,
        "last_known_price": round(float(cdf["y"].iloc[-1]), 2),
        "last_known_date": str(last_data_date.date()),
        "forecast_start_date": str(start_date),
        "forecast": [
            {
                "date": str(row["ds"].date()),
                "predicted_price": round(float(row["yhat"]), 2),
                "lower_bound": round(float(row["yhat_lower"]), 2),
                "upper_bound": round(float(row["yhat_upper"]), 2),
            }
            for _, row in forecast_window.iterrows()
        ],
        "trend": (
            "rising"
            if forecast_window["yhat"].iloc[-1] > forecast_window["yhat"].iloc[0]
            else "falling"
        ),
        "avg_forecast_price": round(float(forecast_window["yhat"].mean()), 2),
    }

    return result, forecast, model


# ── Batch forecasting ─────────────────────────────────────────
def run_all_forecasts(
    filepath: str,
    top_n: int = 10,
    start_date: date = None,
    forecast_days: int = 7,
) -> dict:
    """Runs forecast for top N commodities and saves forecasts.json."""
    if start_date is None:
        start_date = date.today()

    df = load_karnataka_data(filepath)
    top_commodities = df["commodity"].value_counts().head(top_n).index.tolist()

    all_forecasts = {}
    for commodity in top_commodities:
        print(f"Forecasting: {commodity} (start: {start_date})")
        cdf = get_commodity_df(df, commodity)
        try:
            result, _, _ = forecast_commodity(
                cdf, commodity,
                forecast_days=forecast_days,
                start_date=start_date,
            )
            all_forecasts[commodity] = result
            print(f"  ✓ freq={result.get('data_frequency')}  trend={result['trend']}  avg=₹{result['avg_forecast_price']}")
        except Exception as e:
            print(f"  FAILED: {e}")
            all_forecasts[commodity] = {"error": str(e)}

    with open("forecasts.json", "w") as f:
        json.dump(all_forecasts, f, indent=2, default=str)

    print(f"\nSaved forecasts.json ({len(all_forecasts)} commodities)")
    return all_forecasts


# ── Debug helper ──────────────────────────────────────────────
def check_data_frequency(filepath: str, commodity: str):
    """Run this first to confirm daily vs monthly: python forecaster.py check Tomato"""
    df  = load_karnataka_data(filepath)
    cdf = get_commodity_df(df, commodity)
    gaps = cdf["ds"].sort_values().diff().dt.days.dropna()
    print(f"\nFrequency check — {commodity}")
    print(f"  Rows        : {len(cdf)}")
    print(f"  Date range  : {cdf['ds'].min().date()} → {cdf['ds'].max().date()}")
    print(f"  Median gap  : {gaps.median():.0f} days")
    print(f"  Detected    : {detect_freq(cdf)}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        commodity = sys.argv[2] if len(sys.argv) > 2 else "Tomato"
        check_data_frequency("data/karnataka_raw.csv", commodity)
    else:
        run_all_forecasts(
            "data/karnataka_raw.csv",
            top_n=10,
            start_date=date.today(),
            forecast_days=7,
        )
