"""
dcf.py
A simple discounted cash flow model. Deliberately transparent: every
assumption is a named, editable input, not buried inside a prompt to an LLM.
This is the part interviewers will poke at hardest — know every line.
"""

from dataclasses import dataclass, field


@dataclass
class DCFAssumptions:
    base_revenue: float            # most recent fiscal year revenue, millions
    revenue_growth_rates: list     # e.g. [0.08, 0.07, 0.06, 0.05, 0.04] for yrs 1-5
    ebitda_margin: float           # e.g. 0.25 for 25%
    tax_rate: float                # e.g. 0.21
    capex_pct_revenue: float       # e.g. 0.05
    da_pct_revenue: float          # depreciation & amortization, e.g. 0.04
    nwc_pct_revenue_change: float  # net working capital as % of revenue change
    discount_rate: float           # WACC, e.g. 0.09
    terminal_growth_rate: float    # e.g. 0.025 (long-run GDP-ish growth)
    net_debt: float                # total debt minus cash, millions
    shares_outstanding: float      # millions


def project_free_cash_flows(a: DCFAssumptions) -> list[dict]:
    """Builds year-by-year unlevered free cash flow projections."""
    projections = []
    revenue = a.base_revenue

    for i, growth in enumerate(a.revenue_growth_rates, start=1):
        prior_revenue = revenue
        revenue = revenue * (1 + growth)

        ebitda = revenue * a.ebitda_margin
        da = revenue * a.da_pct_revenue
        ebit = ebitda - da
        tax = ebit * a.tax_rate
        nopat = ebit - tax  # net operating profit after tax

        capex = revenue * a.capex_pct_revenue
        nwc_change = (revenue - prior_revenue) * a.nwc_pct_revenue_change

        fcf = nopat + da - capex - nwc_change

        projections.append({
            "year": i,
            "revenue": round(revenue, 1),
            "ebitda": round(ebitda, 1),
            "ebit": round(ebit, 1),
            "nopat": round(nopat, 1),
            "fcf": round(fcf, 1),
        })

    return projections


def terminal_value(final_year_fcf: float, a: DCFAssumptions) -> float:
    """Gordon Growth terminal value at the end of the projection period."""
    return (
        final_year_fcf * (1 + a.terminal_growth_rate)
        / (a.discount_rate - a.terminal_growth_rate)
    )


def discount_to_present(value: float, year: int, discount_rate: float) -> float:
    return value / ((1 + discount_rate) ** year)


def run_dcf(a: DCFAssumptions) -> dict:
    projections = project_free_cash_flows(a)
    n_years = len(projections)

    pv_fcfs = [
        discount_to_present(p["fcf"], p["year"], a.discount_rate)
        for p in projections
    ]

    tv = terminal_value(projections[-1]["fcf"], a)
    pv_tv = discount_to_present(tv, n_years, a.discount_rate)

    enterprise_value = sum(pv_fcfs) + pv_tv
    equity_value = enterprise_value - a.net_debt
    implied_share_price = equity_value / a.shares_outstanding

    return {
        "projections": projections,
        "pv_of_fcfs": round(sum(pv_fcfs), 1),
        "terminal_value": round(tv, 1),
        "pv_of_terminal_value": round(pv_tv, 1),
        "enterprise_value": round(enterprise_value, 1),
        "equity_value": round(equity_value, 1),
        "implied_share_price": round(implied_share_price, 2),
        "terminal_value_pct_of_ev": round(pv_tv / enterprise_value * 100, 1),
    }


if __name__ == "__main__":
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

    result = run_dcf(assumptions)
    for k, v in result.items():
        print(f"{k}: {v}")
