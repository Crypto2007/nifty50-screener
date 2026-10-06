import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Complete Nifty 50 Universe (NSE Tickers with .NS suffix for yfinance)
NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "LTIM.NS", "LT.NS",
    "AXISBANK.NS", "KOTAKBANK.NS", "HCLTECH.NS", "ASIANPAINT.NS", "TITAN.NS",
    "SUNPHARMA.NS", "MARUTI.NS", "ULTRACEMCO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "NESTLEIND.NS", "TATAMOTORS.NS", "TATASTEEL.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "M&M.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "HINDUNILVR.NS", "HINDALCO.NS", "GRASIM.NS", "CIPLA.NS", "DRREDDY.NS",
    "APOLLOHOSP.NS", "EICHERMOT.NS", "BPCL.NS", "HEROMOTOCO.NS", "DIVISLAB.NS",
    "TATACONSUM.NS", "SBILIFE.NS", "HDFCLIFE.NS", "WIPRO.NS", "TECHM.NS",
    "JSWSTEEL.NS", "BRITANNIA.NS", "BEL.NS", "TRENT.NS", "SHRIRAMFIN.NS"
]


def fetch_ticker_metrics(ticker_symbol: str) -> Dict[str, Any]:
    """Fetch fundamental metrics for a single NSE ticker via yfinance."""
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info or {}

        # Clean display symbol (e.g., RELIANCE instead of RELIANCE.NS)
        clean_symbol = ticker_symbol.replace(".NS", "")

        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")

        return {
            "ticker": clean_symbol,
            "company_name": info.get("shortName") or info.get("longName") or clean_symbol,
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "market_cap": info.get("marketCap", 0.0),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE") or None,
            "pb_ratio": info.get("priceToBook") or None,
            "ps_ratio": info.get("priceToSalesTrailing12Months") or None,
            "ev_ebitda": info.get("enterpriseToEbitda") or None,
            "roe": info.get("returnOnEquity") or None,
            "roa": info.get("returnOnAssets") or None,
            "gross_margin": info.get("grossMargins") or None,
            "operating_margin": info.get("operatingMargins") or None,
            "net_margin": info.get("profitMargins") or None,
            "revenue_growth": info.get("revenueGrowth") or None,
            "earnings_growth": info.get("earningsGrowth") or None,
            "free_cashflow_yield": (
                (info.get("freeCashflow", 0.0) / info.get("marketCap", 1.0))
                if info.get("marketCap") and info.get("freeCashflow")
                else None
            ),
            "debt_to_equity": info.get("debtToEquity") or None,
            "current_ratio": info.get("currentRatio") or None,
            "quick_ratio": info.get("quickRatio") or None,
            "dividend_yield": info.get("dividendYield") or None,
            "payout_ratio": info.get("payoutRatio") or None,
            "beta": info.get("beta") or None,
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh") or None,
            "fifty_two_week_low": info.get("fiftyTwoWeekLow") or None,
            "current_price": float(price) if price is not None else None,
        }
    except Exception as err:
        logger.warning("Failed to fetch metrics for %s: %s", ticker_symbol, err)
        return {"ticker": ticker_symbol.replace(".NS", ""), "company_name": ticker_symbol}


def fetch_universe_data(tickers: List[str] = None, max_workers: int = 10) -> pd.DataFrame:
    """Concurrently fetch metrics for all Nifty 50 constituents."""
    symbols = tickers if tickers else NIFTY_50_TICKERS
    records = []

    # Use ThreadPoolExecutor to fetch 50 tickers fast in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_symbol = {executor.submit(fetch_ticker_metrics, sym): sym for sym in symbols}
        for future in as_completed(future_to_symbol):
            res = future.result()
            if res:
                records.append(res)

    df = pd.DataFrame(records)
    logger.info("Successfully fetched %d Nifty 50 stocks.", len(df))
    return df