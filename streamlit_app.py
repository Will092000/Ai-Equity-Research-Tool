"""
streamlit_app.py
Web interface for the equity research pipeline. Wraps comps.py, dcf.py,
and memo.py with input fields instead of hardcoded example numbers.

Run locally: streamlit run streamlit_app.py
Deploy: push to GitHub, then deploy via share.streamlit.io pointing at
this file. Set OPENROUTER_API_KEY as a "Secret" in the Streamlit Cloud
app settings (Settings -> Secrets) — do NOT hardcode it here.
"""

import os
import streamlit as st

from comps import CompanySnapshot, build_comps_table
from dcf import DCFAssumptions, run_dcf
from memo import generate_memo

st.set_page_config(page_title="AI Equity Research Tool", layout="wide")

# On Streamlit Cloud, secrets are exposed via st.secrets, not just
# os.environ. Support both so this works locally (export in terminal)
# and when deployed (set as a Secret in the app's settings).
if "OPENROUTER_API_KEY" in st.secrets:
    os.environ["OPENROUTER_API_KEY"] = st.secrets["OPENROUTER_API_KEY"]

st.title("AI-Assisted Equity Research Tool")
st.caption(
    "Comps and DCF math are fully deterministic — the AI only writes "
    "the summary memo from numbers already calculated below."
)

# ---------------------------------------------------------------------
# INPUTS
# ---------------------------------------------------------------------
st.header("1. Target Company")

col1, col2, col3, col4 = st.columns(4)
with col1:
    ticker = st.text_input("Ticker", value="EXMP")
    share_price = st.number_input("Share price ($)", value=100.0, min_value=0.0)
with col2:
    shares_out = st.number_input("Shares outstanding (millions)", value=500.0, min_value=0.0)
    total_debt = st.number_input("Total debt ($M)", value=2000.0, min_value=0.0)
with col3:
    cash = st.number_input("Cash & equivalents ($M)", value=500.0, min_value=0.0)
    revenue = st.number_input("Revenue, TTM ($M)", value=8000.0, min_value=0.0)
with col4:
    ebitda = st.number_input("EBITDA, TTM ($M)", value=1600.0, min_value=0.0)
    net_income = st.number_input("Net income, TTM ($M)", value=900.0, min_value=0.0)

st.header("2. Peer Companies (for comps)")
st.caption("Add 2-4 peers. More peers = a more reliable comps benchmark.")

num_peers = st.number_input("Number of peers", min_value=1, max_value=6, value=2, step=1)

peers = []
peer_cols = st.columns(int(num_peers))
for i, col in enumerate(peer_cols):
    with col:
        st.markdown(f"**Peer {i + 1}**")
        p_ticker = st.text_input("Ticker", value=f"PEER{i + 1}", key=f"pt{i}")
        p_price = st.number_input("Price ($)", value=90.0, min_value=0.0, key=f"pp{i}")
        p_shares = st.number_input("Shares (M)", value=500.0, min_value=0.0, key=f"ps{i}")
        p_debt = st.number_input("Debt ($M)", value=1500.0, min_value=0.0, key=f"pd{i}")
        p_cash = st.number_input("Cash ($M)", value=400.0, min_value=0.0, key=f"pc{i}")
        p_rev = st.number_input("Revenue ($M)", value=7000.0, min_value=0.0, key=f"pr{i}")
        p_ebitda = st.number_input("EBITDA ($M)", value=1400.0, min_value=0.0, key=f"pe{i}")
        p_ni = st.number_input("Net income ($M)", value=750.0, min_value=0.0, key=f"pn{i}")
        peers.append(
            CompanySnapshot(
                ticker=p_ticker, share_price=p_price, shares_outstanding=p_shares,
                total_debt=p_debt, cash_and_equivalents=p_cash,
                revenue=p_rev, ebitda=p_ebitda, net_income=p_ni,
            )
        )

st.header("3. DCF Assumptions")

col1, col2, col3 = st.columns(3)
with col1:
    growth_y1 = st.slider("Year 1 growth %", 0.0, 30.0, 8.0) / 100
    growth_y5 = st.slider("Year 5 growth %", 0.0, 30.0, 4.0) / 100
    ebitda_margin = st.slider("EBITDA margin %", 0.0, 60.0, 25.0) / 100
with col2:
    tax_rate = st.slider("Tax rate %", 0.0, 40.0, 21.0) / 100
    discount_rate = st.slider("Discount rate / WACC %", 1.0, 20.0, 9.0) / 100
    terminal_growth = st.slider("Terminal growth %", 0.0, 5.0, 2.5) / 100
with col3:
    capex_pct = st.slider("CapEx % of revenue", 0.0, 20.0, 5.0) / 100
    da_pct = st.slider("D&A % of revenue", 0.0, 20.0, 4.0) / 100
    nwc_pct = st.slider("NWC % of revenue change", 0.0, 30.0, 10.0) / 100

# Linear interpolation between year-1 and year-5 growth for a smooth ramp
growth_rates = [
    growth_y1 + (growth_y5 - growth_y1) * (i / 4) for i in range(5)
]

# ---------------------------------------------------------------------
# RUN
# ---------------------------------------------------------------------
st.header("4. Run Analysis")

if st.button("Run Analysis", type="primary"):
    if not os.environ.get("OPENROUTER_API_KEY"):
        st.error(
            "No OPENROUTER_API_KEY found. Set it as a Secret in your "
            "Streamlit Cloud app settings, or export it locally before "
            "running `streamlit run streamlit_app.py`."
        )
    else:
        target = CompanySnapshot(
            ticker=ticker, share_price=share_price, shares_outstanding=shares_out,
            total_debt=total_debt, cash_and_equivalents=cash,
            revenue=revenue, ebitda=ebitda, net_income=net_income,
        )

        with st.spinner("Calculating comps..."):
            comps_result = build_comps_table(target, peers)

        with st.spinner("Running DCF..."):
            assumptions = DCFAssumptions(
                base_revenue=revenue,
                revenue_growth_rates=growth_rates,
                ebitda_margin=ebitda_margin,
                tax_rate=tax_rate,
                capex_pct_revenue=capex_pct,
                da_pct_revenue=da_pct,
                nwc_pct_revenue_change=nwc_pct,
                discount_rate=discount_rate,
                terminal_growth_rate=terminal_growth,
                net_debt=total_debt - cash,
                shares_outstanding=shares_out,
            )
            dcf_result = run_dcf(assumptions)

        st.subheader("Comps Results")
        st.json(comps_result)

        st.subheader("DCF Results")
        st.json(dcf_result)

        with st.spinner("Generating memo (this can take 15-30s on the free tier)..."):
            try:
                memo_text = generate_memo(ticker, comps_result, dcf_result)
                st.subheader("Summary Memo")
                st.markdown(memo_text)
            except Exception as e:
                st.error(f"Memo generation failed: {e}")

st.divider()
st.caption(
    "Data entry is manual by design — this is a modeling/analysis tool, "
    "not a live market data feed. Source your numbers from 10-Ks, "
    "earnings releases, or a finance data site before running."
)
