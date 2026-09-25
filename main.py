"""
main.py
Wires the full pipeline together: pull data -> build comps -> run DCF ->
generate memo. This is a template — you'll need to fill in real peer data
and DCF assumptions per company since those require judgment calls that
shouldn't be automated away.
"""

from comps import CompanySnapshot, build_comps_table
from dcf import DCFAssumptions, run_dcf
from memo import generate_memo


def analyze_company(
    ticker: str,
    target_snapshot: CompanySnapshot,
    peer_snapshots: list,
    dcf_assumptions: DCFAssumptions,
) -> dict:
    """
    Runs the full pipeline for one company. You provide the snapshot data
    and DCF assumptions yourself (this is the "analyst judgment" part —
    deciding on peers and growth assumptions is real work, not automation).
    """
    print(f"Building comps table for {ticker}...")
    comps_result = build_comps_table(target_snapshot, peer_snapshots)

    print(f"Running DCF for {ticker}...")
    dcf_result = run_dcf(dcf_assumptions)

    print(f"Generating memo for {ticker}...")
    memo_text = generate_memo(ticker, comps_result, dcf_result)

    return {
        "ticker": ticker,
        "comps": comps_result,
        "dcf": dcf_result,
        "memo": memo_text,
    }


if __name__ == "__main__":
    # EXAMPLE RUN — replace with real pulled/researched data for an actual
    # company. This uses made-up placeholder numbers to show the pipeline
    # working end to end.

    target = CompanySnapshot(
        ticker="EXMP", share_price=100, shares_outstanding=500,
        total_debt=2000, cash_and_equivalents=500,
        revenue=8000, ebitda=1600, net_income=900,
    )
    peers = [
        CompanySnapshot("PEER1", 80, 600, 1500, 300, 7000, 1400, 750),
        CompanySnapshot("PEER2", 120, 400, 1000, 600, 6000, 1300, 700),
    ]
    assumptions = DCFAssumptions(
        base_revenue=8000,
        revenue_growth_rates=[0.08, 0.07, 0.06, 0.05, 0.04],
        ebitda_margin=0.25,
        tax_rate=0.21,
        capex_pct_revenue=0.05,
        da_pct_revenue=0.04,
        nwc_pct_revenue_change=0.10,
        discount_rate=0.09,
        terminal_growth_rate=0.025,
        net_debt=1500,
        shares_outstanding=500,
    )

    result = analyze_company("EXMP", target, peers, assumptions)

    print("\n" + "=" * 60)
    print(f"SUMMARY MEMO — {result['ticker']}")
    print("=" * 60)
    print(result["memo"])
