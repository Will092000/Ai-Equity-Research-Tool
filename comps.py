"""
comps.py
Calculates comparable-company valuation multiples.
This is pure arithmetic — deliberately no AI involved here. The numbers
that go into an interview conversation need to be numbers YOU calculated,
not numbers an LLM guessed at.
"""

from dataclasses import dataclass


@dataclass
class CompanySnapshot:
    """Minimal set of figures needed for basic comps. Pull these from
    data_pull.py (financials) and a market data API (price/shares/debt/cash)."""
    ticker: str
    share_price: float
    shares_outstanding: float  # in millions
    total_debt: float          # in millions
    cash_and_equivalents: float  # in millions
    revenue: float              # trailing twelve months, in millions
    ebitda: float                # trailing twelve months, in millions
    net_income: float           # trailing twelve months, in millions

    @property
    def market_cap(self) -> float:
        return self.share_price * self.shares_outstanding

    @property
    def enterprise_value(self) -> float:
        return self.market_cap + self.total_debt - self.cash_and_equivalents

    @property
    def ev_ebitda(self) -> float | None:
        return self.enterprise_value / self.ebitda if self.ebitda else None

    @property
    def ev_revenue(self) -> float | None:
        return self.enterprise_value / self.revenue if self.revenue else None

    @property
    def pe_ratio(self) -> float | None:
        return self.market_cap / self.net_income if self.net_income else None


def build_comps_table(target: CompanySnapshot, peers: list[CompanySnapshot]) -> dict:
    """
    Returns the target's multiples alongside peer average/median multiples —
    the standard "how does this company trade vs. its peer set" table.
    """
    def avg(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    def median(vals):
        vals = sorted(v for v in vals if v is not None)
        n = len(vals)
        if n == 0:
            return None
        mid = n // 2
        return vals[mid] if n % 2 else (vals[mid - 1] + vals[mid]) / 2

    peer_ev_ebitda = [p.ev_ebitda for p in peers]
    peer_ev_revenue = [p.ev_revenue for p in peers]
    peer_pe = [p.pe_ratio for p in peers]

    return {
        "target": target.ticker,
        "target_ev_ebitda": target.ev_ebitda,
        "target_ev_revenue": target.ev_revenue,
        "target_pe": target.pe_ratio,
        "peer_avg_ev_ebitda": avg(peer_ev_ebitda),
        "peer_median_ev_ebitda": median(peer_ev_ebitda),
        "peer_avg_ev_revenue": avg(peer_ev_revenue),
        "peer_avg_pe": avg(peer_pe),
        "implied_ev_from_peer_ebitda_multiple": (
            median(peer_ev_ebitda) * target.ebitda if median(peer_ev_ebitda) else None
        ),
    }


if __name__ == "__main__":
    # Example with made-up numbers — replace with real pulled data
    target = CompanySnapshot("EXMP", 100, 500, 2000, 500, 8000, 1600, 900)
    peer1 = CompanySnapshot("PEER1", 80, 600, 1500, 300, 7000, 1400, 750)
    peer2 = CompanySnapshot("PEER2", 120, 400, 1000, 600, 6000, 1300, 700)

    table = build_comps_table(target, [peer1, peer2])
    for k, v in table.items():
        print(f"{k}: {v}")
