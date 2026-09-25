"""
data_pull.py
Pulls company financial data from SEC EDGAR's free XBRL "company facts" API.
No API key required — just a proper User-Agent header (SEC requires this).

SEC EDGAR docs: https://www.sec.gov/edgar/sec-api-documentation
"""

import requests

HEADERS = {
    # SEC requires a real identifying User-Agent — put your own name/email here
    "User-Agent": "Your Name your_email@example.com"
}

# You need each company's 10-digit CIK number (SEC's internal company ID).
# Lookup table: https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany
# or use the ticker-to-CIK mapping file below.
TICKER_TO_CIK_URL = "https://www.sec.gov/files/company_tickers.json"


def get_cik_for_ticker(ticker: str) -> str:
    """Look up a company's 10-digit zero-padded CIK from its ticker."""
    resp = requests.get(TICKER_TO_CIK_URL, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    ticker = ticker.upper()
    for entry in data.values():
        if entry["ticker"] == ticker:
            return str(entry["cik_str"]).zfill(10)
    raise ValueError(f"Ticker {ticker} not found in SEC ticker list")


def get_company_facts(cik: str) -> dict:
    """Pull all reported XBRL facts (financial line items) for a company."""
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def extract_metric(facts: dict, tag: str, unit: str = "USD") -> list[dict]:
    """
    Pull a specific line item's historical values, e.g. tag="Revenues" or
    tag="NetIncomeLoss". Common tags live under facts["facts"]["us-gaap"].
    Returns a list of {end date, value, fiscal year, form type} dicts.
    """
    try:
        entries = facts["facts"]["us-gaap"][tag]["units"][unit]
    except KeyError:
        return []
    # Keep only annual figures (10-K) to avoid messy quarterly duplicates
    return [e for e in entries if e.get("form") == "10-K"]


def get_key_financials(ticker: str) -> dict:
    """
    Convenience wrapper: pulls revenue, net income, and shares outstanding
    history for a ticker. Extend with more us-gaap tags as needed —
    common ones: Assets, Liabilities, StockholdersEquity, EBIT is not a
    standard tag (derive it from OperatingIncomeLoss instead).
    """
    cik = get_cik_for_ticker(ticker)
    facts = get_company_facts(cik)

    return {
        "ticker": ticker.upper(),
        "cik": cik,
        "revenue": extract_metric(facts, "Revenues"),
        "operating_income": extract_metric(facts, "OperatingIncomeLoss"),
        "net_income": extract_metric(facts, "NetIncomeLoss"),
        "shares_outstanding": extract_metric(
            facts, "CommonStockSharesOutstanding", unit="shares"
        ),
    }


if __name__ == "__main__":
    # Quick test
    data = get_key_financials("AAPL")
    print(f"CIK: {data['cik']}")
    print(f"Most recent revenue entries: {data['revenue'][-3:]}")
