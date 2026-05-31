import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json
import os
from datetime import date, timedelta
from data_loader import load_karnataka_data, get_commodity_df
from forecaster import forecast_commodity
from advisory import generate_kannada_advisory

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="Karnataka Mandi Price Forecast",
    page_icon="🌾",
    layout="wide"
)

# ── Load data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    return load_karnataka_data("data/karnataka_raw.csv")

@st.cache_data
def load_advisories():
    if os.path.exists("advisories.json"):
        with open("advisories.json", encoding="utf-8") as f:
            return json.load(f)
    return {}

df         = load_data()
advisories = load_advisories()

# ── Header ────────────────────────────────────────────────────
st.title("🌾 Karnataka Mandi Price Forecast")
st.caption("Data: CEDA Agri Market Data (CEDA-AMD), Ashoka University | Forecast: Prophet | Advisory: Groq AI (Kannada)")

# ── Sidebar ───────────────────────────────────────────────────
st.sidebar.header("Filters")

# District filter
all_districts = sorted(df["district"].dropna().unique().tolist()) if "district" in df.columns else []
district_options = ["All Karnataka"] + all_districts
selected_district = st.sidebar.selectbox("District", district_options)

# Commodity filter — respects district selection
if selected_district != "All Karnataka" and "district" in df.columns:
    district_df = df[df["district"].str.lower() == selected_district.lower()]
else:
    district_df = df

commodities = sorted(district_df["commodity"].dropna().unique().tolist())
if not commodities:
    st.warning("No commodities found for this district. Showing all Karnataka.")
    commodities = sorted(df["commodity"].dropna().unique().tolist())
    district_df = df

selected_commodity = st.sidebar.selectbox("Commodity", commodities)

# Date picker
st.sidebar.markdown("---")
st.sidebar.subheader("Forecast Period")

today = date.today()
start_date = st.sidebar.date_input(
    "Forecast start date",
    value=today,
    min_value=today,
    max_value=today + timedelta(days=90),
    help="Choose the date from which you want the price forecast to begin."
)
forecast_days = st.sidebar.slider("Forecast days", min_value=3, max_value=14, value=7)

# ── Nearest Mandi ─────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.subheader("Nearest Mandis")

if "market" in df.columns:
    # Filter to selected commodity + district (or all Karnataka)
    mandi_filter = df["commodity"].str.lower() == selected_commodity.lower()
    if selected_district != "All Karnataka":
        mandi_filter &= df["district"].str.lower() == selected_district.lower()

    mandi_df = df[mandi_filter]

    if mandi_df.empty and selected_district != "All Karnataka":
        # No data in this district for this commodity — show all-Karnataka mandis
        st.sidebar.caption(f"No mandis in {selected_district} for {selected_commodity}. Showing all Karnataka.")
        mandi_df = df[df["commodity"].str.lower() == selected_commodity.lower()]

    if not mandi_df.empty:
        latest_per_mandi = (
            mandi_df.sort_values("date")
            .groupby("market", sort=False)
            .agg(latest_price=("modal_price", "last"), latest_date=("date", "last"))
            .reset_index()
            .sort_values("latest_date", ascending=False)
        )
        for _, row in latest_per_mandi.iterrows():
            st.sidebar.markdown(
                f"**{row['market']}**  \n"
                f"₹{row['latest_price']:,.0f} &nbsp;·&nbsp; {row['latest_date'].strftime('%d %b %Y')}"
            )
    else:
        st.sidebar.info("No mandi data found.")
else:
    st.sidebar.info("Market column not available in dataset.")

# ── Main layout ───────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"Price Forecast: {selected_commodity}")
    if selected_district != "All Karnataka":
        st.caption(f"District: {selected_district}")

    # Use district-filtered data; fall back to all-Karnataka if too few rows
    cdf = get_commodity_df(district_df, selected_commodity)
    if len(cdf) < 30:
        st.info(f"Not enough district-level data for {selected_commodity}. Using Karnataka-wide data.")
        cdf = get_commodity_df(df, selected_commodity)

    if len(cdf) < 30:
        st.warning(f"Not enough data for {selected_commodity} (only {len(cdf)} rows). Need at least 30.")
    else:
        last_data_date = cdf["ds"].max().date()
        days_to_start  = (start_date - last_data_date).days

        if days_to_start < 0:
            st.info(
                f"Chosen start date ({start_date}) is within training data "
                f"(last record: {last_data_date}). Showing forecast from {last_data_date}."
            )
            effective_start = last_data_date
            actual_periods  = forecast_days
        else:
            effective_start = start_date
            actual_periods  = days_to_start + forecast_days

        with st.spinner("Running forecast..."):
            result, forecast_df, model = forecast_commodity(
                cdf,
                selected_commodity,
                forecast_days=actual_periods,
                start_date=effective_start,
            )

        if isinstance(result, dict) and "error" in result:
            st.error(result["error"])
        else:
            forecast_df["ds"] = pd.to_datetime(forecast_df["ds"])
            effective_start_dt = pd.Timestamp(effective_start)
            forecast_window = (
                forecast_df[forecast_df["ds"] >= effective_start_dt]
                .head(forecast_days)
            )

            if forecast_window.empty:
                st.error("Could not generate forecast for the selected date. Try an earlier date.")
            else:
                avg_price = round(float(forecast_window["yhat"].mean()), 2)

                # ── Chart ─────────────────────────────────────
                fig = go.Figure()

                hist = cdf.tail(90)
                fig.add_trace(go.Scatter(
                    x=hist["ds"], y=hist["y"],
                    mode="lines", name="Historical price",
                    line=dict(color="#1f77b4", width=1.5)
                ))

                fig.add_trace(go.Scatter(
                    x=forecast_window["ds"], y=forecast_window["yhat"],
                    mode="lines+markers", name=f"Forecast (from {effective_start})",
                    line=dict(color="#ff7f0e", width=2, dash="dash")
                ))

                fig.add_trace(go.Scatter(
                    x=pd.concat([forecast_window["ds"], forecast_window["ds"][::-1]]),
                    y=pd.concat([forecast_window["yhat_upper"], forecast_window["yhat_lower"][::-1]]),
                    fill="toself", fillcolor="rgba(255,127,14,0.15)",
                    line=dict(color="rgba(255,255,255,0)"),
                    name="80% confidence band"
                ))

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Price (₹/Quintal)",
                    legend=dict(orientation="h"),
                    hovermode="x unified",
                    height=400,
                )
                st.plotly_chart(fig, use_container_width=True)

                # ── Forecast table ─────────────────────────────
                st.subheader("Forecast Table")
                forecast_table = forecast_window[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
                forecast_table.columns = ["Date", "Predicted price (₹)", "Lower bound (₹)", "Upper bound (₹)"]
                forecast_table["Date"] = forecast_table["Date"].dt.strftime("%d %b %Y")
                forecast_table = forecast_table.reset_index(drop=True)
                st.dataframe(forecast_table, use_container_width=True)

with col2:
    st.subheader("📢 ಕನ್ನಡ ಸಲಹೆ")

    if len(cdf) >= 30 and "forecast_window" in dir() and not forecast_window.empty:
        forecast_data_for_advisory = {
            "commodity": selected_commodity,
            "last_known_price": float(cdf["y"].iloc[-1]),
            "last_known_date": str(cdf["ds"].iloc[-1].date()),
            "trend": result.get("trend", "stable") if isinstance(result, dict) else "stable",
            "avg_forecast_price": avg_price,
            "forecast": [
                {
                    "date": str(row["ds"].date()),
                    "predicted_price": round(float(row["yhat"]), 2),
                }
                for _, row in forecast_window.iterrows()
            ],
        }

        cache_key = f"{selected_commodity}_{selected_district}_{start_date}"
        if cache_key in advisories:
            advisory_text = advisories[cache_key]
        elif selected_commodity in advisories:
            advisory_text = advisories[selected_commodity]
        else:
            with st.spinner("Generating Kannada advisory..."):
                try:
                    advisory_text = generate_kannada_advisory(forecast_data_for_advisory)
                except Exception as e:
                    advisory_text = "ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ"
                    st.error(f"Advisory generation failed: {e}")
    else:
        advisory_text = "ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ"

    st.info(advisory_text)

    # ── Key stats ──────────────────────────────────────────────
    st.subheader("Key stats")
    if len(cdf) >= 30 and "forecast_window" in dir() and not forecast_window.empty:
        last_price = float(cdf["y"].iloc[-1])
        trend_icon = "📈" if isinstance(result, dict) and result.get("trend") == "rising" else "📉"
        pct_change = round(((avg_price - last_price) / last_price) * 100, 1) if last_price else 0

        st.metric("Last known price", f"₹{last_price:,.0f}")
        st.metric(
            f"Avg forecast ({forecast_days}d from {effective_start})",
            f"₹{avg_price:,.0f}",
            delta=f"{pct_change:+.1f}%"
        )
        st.metric("Trend", f"{trend_icon} {result.get('trend', 'unknown').capitalize()}")
        st.metric("Last data date", str(last_data_date))
        if days_to_start > 0:
            st.metric("Days bridged", days_to_start)

# ── Footer ─────────────────────────────────────────────────────
st.divider()
st.caption(
    "Data: CEDA Agri Market Data (CEDA-AMD), 2000–2026. "
    "Centre for Economic Data & Analysis, Ashoka University. "
    "For hackathon demonstration only."
)
