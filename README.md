# AI-Assisted Equity Research Tool — Starter

A small pipeline that mimics the core grunt work of a junior IB/equity
research analyst: pull company financials, build a comps table, run a DCF,
and generate an analyst-style summary memo — with AI used *only* for the
writing step, never for the math.

## Why this design

The credibility of this project rests on one decision: **the AI never
calculates anything.** `comps.py` and `dcf.py` are pure, deterministic
Python — the same numbers, every time, that you can defend line by line.
`memo.py` is the only place an LLM touches the pipeline, and it's only
asked to write prose about numbers it's handed, not to invent them.

This mirrors how AI is actually being deployed at real banks right now:
automating formatting/summarization, while the underlying financial logic
stays human- (or deterministic-code-) owned.

## Files

- `data_pull.py` — pulls financials from SEC EDGAR's free API (no key needed)
- `comps.py` — calculates comparable-company valuation multiples
- `dcf.py` — runs a discounted cash flow model from transparent assumptions
- `memo.py` — sends calculated results to Claude to draft a summary memo
- `main.py` — wires the pieces together end to end

## Setup

```bash
pip install requests
export OPENROUTER_API_KEY="your-key-here"
```

Get a free API key at https://openrouter.ai (Keys section, no payment
required). `memo.py` uses a free-tier model by default — check
https://openrouter.ai/models?max_price=0 if the model referenced in
`memo.py` is no longer available and swap in a current free one.

## Running it

Each module runs standalone for testing:
```bash
python data_pull.py   # test SEC data pull for AAPL
python comps.py        # test comps math with example numbers
python dcf.py           # test DCF math with example assumptions
python memo.py          # test memo generation with example results
```

Once each piece works, use `main.py` to run the full pipeline on a real
ticker end to end.

## Known gaps to fill in yourself (this is intentional — these are good
## things to have opinions about in an interview)

1. **`data_pull.py` only pulls from SEC filings**, which lag real-time
   and don't include share price. You'll need a market data API
   (Alpha Vantage, Financial Modeling Prep, or similar — most have free
   tiers) for live price, shares outstanding, and peer selection.

2. **SEC XBRL tags aren't fully standardized across companies** — e.g.
   some companies report revenue under `Revenues`, others under
   `RevenueFromContractWithCustomerExcludingAssessedTax`. You'll need to
   handle fallback tags per company. This is a real, annoying part of
   working with SEC data — expect to spend time here.

3. **Peer selection is manual** in this starter (you pass in a list of
   `CompanySnapshot` objects). A more advanced version could pull an
   industry/sector classification and auto-select peers — good v2 feature.

4. **No error handling for missing data** yet — add it as you go.

## Suggested next steps

1. Get `data_pull.py` working end to end for 1 real company
2. Manually gather share price + peer data for that company, run `comps.py`
3. Build DCF assumptions for that same company, run `dcf.py`
4. Generate a memo, read it critically — does it sound like a real analyst
   wrote it, or does it hedge/waffle? Tighten the prompt if needed
5. Repeat for 3-4 more companies
6. Write up your methodology doc — this is what you'll actually discuss
   in interviews
