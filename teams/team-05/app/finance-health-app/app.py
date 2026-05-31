"""
Personal Finance Health Report Generator — Streamlit app.

Run with:
    streamlit run app.py

Flow:
    1. User fills the form across 4 tabs (Profile, Income & Expenses, Debts, Assets)
    2. Submit triggers compute_wellness_score (deterministic, fast)
    3. Plotly charts render
    4. LLM generates narrative + 3 recommendations
    5. DOCX report assembled and offered as download
"""

from __future__ import annotations

import io
import json
import logging
from datetime import datetime

import plotly.graph_objects as go
import streamlit as st

from models import (
    FinancialProfile,
    IncomeInfo,
    Expenses,
    Debt,
    Savings,
    Investments,
    WellnessScore,
    RecommendationSet,
)
from score import compute_wellness_score
from benchmarks import expected_spending_inr
from llm import generate_narrative, generate_recommendations
from report import build_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("app")


# ---------- Page config ----------

st.set_page_config(
    page_title="Personal Finance Health Report",
    page_icon="₹",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Caching wrappers ----------
# Cache by profile JSON hash so dev iterations don't burn LLM quota.

@st.cache_data(show_spinner=False)
def _cached_narrative(profile_json: str, score_total: float) -> str:
    profile = FinancialProfile.model_validate_json(profile_json)
    score = compute_wellness_score(profile)
    return generate_narrative(profile, score)


@st.cache_data(show_spinner=False)
def _cached_recommendations(profile_json: str, score_total: float) -> str:
    """Cached as JSON string because RecommendationSet isn't directly hashable."""
    profile = FinancialProfile.model_validate_json(profile_json)
    score = compute_wellness_score(profile)
    return generate_recommendations(profile, score).model_dump_json()


# ---------- Sidebar ----------

with st.sidebar:
    st.markdown("""
    <div style="margin-bottom: 2rem;">
        <h2 style="font-size: 1.25rem; font-weight: 600; color: #3b82f6; display: flex; align-items: center; gap: 8px;">🛡️ FinanceGen</h2>
        <p style="color: #a1a1aa; font-size: 0.85rem; margin-top: -5px;">Enterprise Financial Wellness</p>
    </div>
    
    <div style="background-color: rgba(24,24,27,0.5); padding: 1rem; border-radius: 8px; border: 1px solid #27272a; margin-bottom: 2rem;">
        <p style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #a1a1aa; margin-bottom: 0.5rem;"><b>Execution Pipeline</b></p>
        <ul style="color: #d4d4d8; font-size: 0.85rem; padding-left: 1rem; margin: 0; line-height: 1.6;">
            <li>Data Validation (Pydantic)</li>
            <li>Deterministic Engine Math</li>
            <li>NSSO Benchmark Fetch</li>
            <li>LLaMA-3 Strategic Synthesis</li>
            <li>DOCX Report Compilation</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.button("🔄 Load sample profile", use_container_width=True):
        with open("data/sample_profile.json") as f:
            sample = json.load(f)
        st.session_state["sample"] = sample
        st.rerun()


# ---------- Main ----------

st.markdown("""
<div style="padding: 1rem 0 2rem 0; border-bottom: 1px solid #27272a; margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem; font-weight: 700; color: #f4f4f5; margin-bottom: 0.25rem; letter-spacing: -0.03em;">FinanceGen Core</h1>
    <p style="color: #a1a1aa; font-size: 1.05rem; margin: 0;">Automated financial diagnostic overview and LLM strategic synthesis.</p>
</div>
""", unsafe_allow_html=True)


# ---------- Form ----------

sample = st.session_state.get("sample", {})

with st.form("finance_form", clear_on_submit=False):
    tab_p, tab_ie, tab_d, tab_a = st.tabs(
        ["👤 Profile", "💰 Income & Expenses", "💳 Debts", "🏦 Savings & Investments"]
    )

    # --- Profile tab ---
    with tab_p:
        c1, c2, c3 = st.columns(3)
        with c1:
            user_name = st.text_input(
                "Your name", value=sample.get("user_name", ""), placeholder="e.g. Name"
            )
            age = st.number_input(
                "Age", min_value=18, max_value=100, value=sample.get("age", 28), step=1
            )
        with c2:
            dependents = st.number_input(
                "Number of dependents", min_value=0, max_value=20,
                value=sample.get("dependents", 0), step=1
            )
            city_tier_label = st.selectbox(
                "City tier",
                ["Tier 1 (metro)", "Tier 2", "Tier 3"],
                index={"tier1": 0, "tier2": 1, "tier3": 2}.get(sample.get("city_tier", "tier1"), 0),
                help="Tier 1 = Bangalore/Mumbai/Delhi etc. Affects benchmark comparison.",
            )
        city_tier = {"Tier 1 (metro)": "tier1", "Tier 2": "tier2", "Tier 3": "tier3"}[city_tier_label]

    # --- Income & Expenses ---
    with tab_ie:
        st.markdown("**Income (₹ per month, take-home)**")
        c1, c2 = st.columns(2)
        with c1:
            monthly_salary = st.number_input(
                "Monthly salary", min_value=0.0,
                value=float(sample.get("income", {}).get("monthly_salary", 80000)),
                step=1000.0,
            )
        with c2:
            other_income = st.number_input(
                "Other income (rental, freelance)", min_value=0.0,
                value=float(sample.get("income", {}).get("other_income", 0)),
                step=500.0,
            )

        st.markdown("**Expenses (₹ per month)**")
        ex = sample.get("expenses", {})
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            housing = st.number_input("Housing (rent/utilities)", min_value=0.0,
                                      value=float(ex.get("housing", 20000)), step=500.0)
            food = st.number_input("Food (groceries+dining)", min_value=0.0,
                                   value=float(ex.get("food", 12000)), step=500.0)
        with c2:
            transport = st.number_input("Transport", min_value=0.0,
                                        value=float(ex.get("transport", 5000)), step=500.0)
            healthcare = st.number_input("Healthcare", min_value=0.0,
                                         value=float(ex.get("healthcare", 2000)), step=500.0)
        with c3:
            education = st.number_input("Education", min_value=0.0,
                                        value=float(ex.get("education", 0)), step=500.0)
            entertainment = st.number_input("Entertainment", min_value=0.0,
                                            value=float(ex.get("entertainment", 4000)), step=500.0)
        with c4:
            shopping = st.number_input("Shopping", min_value=0.0,
                                       value=float(ex.get("shopping", 6000)), step=500.0)
            other_exp = st.number_input("Other expenses", min_value=0.0,
                                        value=float(ex.get("other", 2000)), step=500.0)

    # --- Debts ---
    with tab_d:
        st.markdown("**EMIs (add up to 5 — leave name blank to skip)**")
        debts_sample = sample.get("debts", [])
        debts_input: list[Debt] = []
        for i in range(5):
            d = debts_sample[i] if i < len(debts_sample) else {}
            with st.expander(f"Debt {i + 1}{(' — ' + d['name']) if d.get('name') else ''}",
                              expanded=bool(d)):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    dname = st.text_input(
                        f"Name##{i}", value=d.get("name", ""),
                        placeholder="Home Loan / Car Loan / etc.", label_visibility="collapsed",
                    )
                with c2:
                    outstanding = st.number_input(
                        f"Outstanding##{i}", min_value=0.0,
                        value=float(d.get("outstanding", 0)), step=10000.0,
                        help="Remaining principal",
                    )
                with c3:
                    emi = st.number_input(
                        f"Monthly EMI##{i}", min_value=0.0,
                        value=float(d.get("monthly_emi", 0)), step=500.0,
                    )
                with c4:
                    rate = st.number_input(
                        f"Interest rate (%)##{i}", min_value=0.0, max_value=100.0,
                        value=float(d.get("interest_rate", 0)), step=0.1,
                    )
                if dname.strip():
                    debts_input.append(Debt(
                        name=dname.strip(), outstanding=outstanding,
                        monthly_emi=emi, interest_rate=rate,
                    ))

    # --- Savings & Investments ---
    with tab_a:
        sv = sample.get("savings", {})
        inv = sample.get("investments", {})

        st.markdown("**Savings (₹, current balances)**")
        c1, c2 = st.columns(2)
        with c1:
            emergency_fund = st.number_input(
                "Emergency fund (truly liquid)", min_value=0.0,
                value=float(sv.get("emergency_fund", 50000)), step=5000.0,
                help="Savings account + liquid FD you'd touch in an emergency.",
            )
        with c2:
            fixed_deposits = st.number_input(
                "Fixed deposits (locked)", min_value=0.0,
                value=float(sv.get("fixed_deposits", 0)), step=5000.0,
                help="FDs/RDs you wouldn't break for an emergency.",
            )

        st.markdown("**Investments (₹, current portfolio value)**")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            equity_mfs = st.number_input("Equity MFs", min_value=0.0,
                                         value=float(inv.get("equity_mutual_funds", 100000)), step=5000.0)
            stocks = st.number_input("Stocks", min_value=0.0,
                                     value=float(inv.get("stocks", 0)), step=5000.0)
        with c2:
            debt_funds = st.number_input("Debt funds", min_value=0.0,
                                         value=float(inv.get("debt_funds", 0)), step=5000.0)
            ppf_epf = st.number_input("PPF/EPF/NPS", min_value=0.0,
                                      value=float(inv.get("ppf_epf_nps", 80000)), step=5000.0)
        with c3:
            real_estate = st.number_input("Real estate (non-primary)", min_value=0.0,
                                          value=float(inv.get("real_estate", 0)), step=10000.0)
            gold = st.number_input("Gold (physical + SGB)", min_value=0.0,
                                   value=float(inv.get("gold", 0)), step=5000.0)
        with c4:
            other_inv = st.number_input("Other", min_value=0.0,
                                        value=float(inv.get("other", 0)), step=5000.0)

    st.markdown("---")
    submitted = st.form_submit_button("🎯 Generate my Financial Health Report",
                                       type="primary", use_container_width=True)


# ---------- Submission handling ----------

if submitted:
    try:
        profile = FinancialProfile(
            user_name=user_name, age=age, dependents=dependents, city_tier=city_tier,
            income=IncomeInfo(monthly_salary=monthly_salary, other_income=other_income),
            expenses=Expenses(
                housing=housing, food=food, transport=transport, healthcare=healthcare,
                education=education, entertainment=entertainment, shopping=shopping, other=other_exp,
            ),
            debts=debts_input,
            savings=Savings(emergency_fund=emergency_fund, fixed_deposits=fixed_deposits),
            investments=Investments(
                equity_mutual_funds=equity_mfs, stocks=stocks, debt_funds=debt_funds,
                ppf_epf_nps=ppf_epf, real_estate=real_estate, gold=gold, other=other_inv,
            ),
        )
    except Exception as e:
        st.error(f"Couldn't validate your input: {e}")
        st.stop()

    score = compute_wellness_score(profile)
    profile_json = profile.model_dump_json()

    # ---------- Display: Score headline ----------
    st.divider()
    st.subheader("Your Financial Wellness Score")

    c1, c2 = st.columns([1, 2])
    with c1:
        # Gauge chart
        gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score.total,
            domain={"x": [0, 1], "y": [0, 1]},
            number={"suffix": "/100", "font": {"size": 36}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": "rgba(46, 125, 50, 0.8)"},
                "steps": [
                    {"range": [0, 40], "color": "#FFEBEE"},
                    {"range": [40, 55], "color": "#FFF3E0"},
                    {"range": [55, 70], "color": "#FFF9C4"},
                    {"range": [70, 85], "color": "#E8F5E9"},
                    {"range": [85, 100], "color": "#C8E6C9"},
                ],
            },
            title={"text": f"Grade {score.grade}", "font": {"size": 20}},
        ))
        gauge.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(gauge, use_container_width=True)
    with c2:
        st.markdown(f"### {score.headline}")
        for c in score.components:
            cap = "🟢" if c.percentage >= 80 else "🟡" if c.percentage >= 50 else "🔴"
            st.markdown(f"{cap}  **{c.name}** — {c.score:.0f}/{c.max_score:.0f}  ·  {c.explanation}")

    # ---------- Charts ----------
    st.divider()
    st.subheader("Spending Pattern")

    expense_dict = profile.expenses.model_dump()
    benchmark = expected_spending_inr(city_tier, profile.income.total)
    categories = list(expense_dict.keys())
    your_vals = [expense_dict[c] for c in categories]
    bench_vals = [benchmark.get(c, 0) for c in categories]

    c1, c2 = st.columns(2)
    with c1:
        donut = go.Figure(data=[go.Pie(
            labels=[c.title() for c in categories],
            values=your_vals, hole=0.5,
        )])
        donut.update_layout(title="Your expense breakdown", height=380,
                            margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(donut, use_container_width=True)

    with c2:
        compare = go.Figure(data=[
            go.Bar(name="You", x=categories, y=your_vals, marker_color="#2E7D32"),
            go.Bar(name=f"Typical {city_tier}", x=categories, y=bench_vals, marker_color="#90A4AE"),
        ])
        compare.update_layout(
            title=f"You vs typical {city_tier} household", barmode="group",
            height=380, margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="", yaxis_title="₹ per month",
        )
        st.plotly_chart(compare, use_container_width=True)

    # ---------- LLM narrative ----------
    st.divider()
    st.subheader("Your Financial Picture")
    with st.spinner("Analysing your spending pattern…"):
        narrative = _cached_narrative(profile_json, score.total)
    st.markdown(narrative)

    # ---------- LLM recommendations ----------
    st.divider()
    st.subheader("3 Prioritised Recommendations")
    with st.spinner("Generating recommendations…"):
        recs_json = _cached_recommendations(profile_json, score.total)
        recs = RecommendationSet.model_validate_json(recs_json)

    priority_badge = {"high": "🔴 HIGH", "medium": "🟡 MEDIUM", "low": "🟢 LOW"}
    for i, rec in enumerate(recs.recommendations, 1):
        with st.expander(f"**{i}. {rec.title}**  ·  {priority_badge.get(rec.priority, '')}", expanded=(i == 1)):
            st.markdown(f"**Expected impact:** {rec.expected_impact}")
            st.markdown(f"**Why this matters for you:** {rec.rationale}")
            st.markdown("**Action steps:**")
            for step in rec.action_steps:
                st.markdown(f"- {step}")

    # ---------- DOCX download ----------
    st.divider()
    st.subheader("Take it with you")

    # Render charts to PNG for embedding
    chart_pngs: list[bytes] = []
    try:
        chart_pngs.append(gauge.to_image(format="png", width=800, height=400, scale=2))
        chart_pngs.append(donut.to_image(format="png", width=800, height=500, scale=2))
        chart_pngs.append(compare.to_image(format="png", width=900, height=500, scale=2))
    except Exception as e:
        log.warning(f"Chart PNG export failed: {e}")
        st.warning("Chart images couldn't be embedded in the DOCX. The text content is intact.")

    docx_bytes = build_report(profile, score, narrative, recs, chart_pngs)
    fname = f"finance-report-{profile.user_name.split()[0].lower()}-{datetime.now().strftime('%Y-%m')}.docx"
    st.download_button(
        "📄 Download your monthly DOCX report",
        data=docx_bytes,
        file_name=fname,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
        use_container_width=True,
    )
