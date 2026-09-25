"""
memo.py
The ONLY AI-touching part of the pipeline. It receives numbers you already
calculated (from comps.py and dcf.py) and asks an LLM to write them up in
analyst-style prose. The model never calculates anything — it only writes
about numbers you hand it. This separation is the credibility backbone of
the whole project; be ready to explain it in interviews.

Uses OpenRouter's free-tier models (no payment required). Set
OPENROUTER_API_KEY as an environment variable before running:
export OPENROUTER_API_KEY="sk-or-v1-..."

Get a free key at https://openrouter.ai (Keys section). Free models have
rate limits but no cost — look for models tagged ":free" in OpenRouter's
model list, e.g. "openrouter/free" or check
https://openrouter.ai/models?max_price=0 for the current free lineup,
since which models are free changes over time.
"""

import json
import os
import requests

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
# Swap this if your chosen free model changes — check openrouter.ai/models
FREE_MODEL = "openrouter/free"


def generate_memo(ticker: str, comps_result: dict, dcf_result: dict) -> str:
    """
    Feeds calculated comps + DCF outputs to Claude and asks for a short,
    analyst-style summary memo. All figures are computed upstream — the
    model is only asked to interpret and write, not to compute.
    """
    prompt = f"""You are a junior equity research analyst drafting a short
internal summary memo. You are given ALREADY-CALCULATED valuation figures
below. Do not invent, recalculate, or second-guess any numbers — only
interpret and explain them in clear, professional prose, the way a real
analyst memo reads.

Ticker: {ticker}

COMPS ANALYSIS (calculated):
{json.dumps(comps_result, indent=2)}

DCF ANALYSIS (calculated):
{json.dumps(dcf_result, indent=2)}

Write a memo with these sections:
1. Summary (2-3 sentences: how does the DCF-implied value compare to
   peer-multiple-implied value, and what's the headline takeaway?)
2. Comps read (what the peer multiples suggest, in plain language)
3. DCF read (what's driving the DCF value — call out if terminal value
   is doing most of the work, which is a normal thing analysts flag)
4. Key risks / assumptions to sanity-check (2-3 bullet points on what
   would most change this valuation if wrong — e.g. growth assumptions,
   discount rate sensitivity)

Keep it under 350 words. Professional, direct, no fluff."""

    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": FREE_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
        },
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # Example with dummy results — replace with real comps.py / dcf.py output
    fake_comps = {
        "target": "EXMP",
        "target_ev_ebitda": 6.2,
        "peer_avg_ev_ebitda": 7.1,
        "peer_median_ev_ebitda": 6.9,
        "implied_ev_from_peer_ebitda_multiple": 11040,
    }
    fake_dcf = {
        "enterprise_value": 10200,
        "implied_share_price": 18.40,
        "terminal_value_pct_of_ev": 68.5,
    }

    memo = generate_memo("EXMP", fake_comps, fake_dcf)
    print(memo)
