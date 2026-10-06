import time
import logging
import pandas as pd
from fetcher import load_universe, fetch_universe_batch
from quant import calculate_quant_scores

# Configure Pandas terminal options for clean display
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", 1000)

# Optional: Enable logging to view quant debug messages (e.g., NaN fills)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main():
    print("=" * 80)
    print(" QUANTITATIVE STOCK SCREENER ENGINE (PHASE 1 + PHASE 2) ")
    print("=" * 80)

    # 1. Phase 1: Ingestion
    universe_name = "nifty_50"
    tickers = load_universe(universe_name)
    print(f"[Phase 1] Loaded {len(tickers)} tickers for '{universe_name}'.")

    start_time = time.time()
    raw_data = fetch_universe_batch(tickers, max_workers=10)
    ingest_time = time.time() - start_time

    if not raw_data:
        print("[Error] No data fetched. Pipeline aborting.")
        return

    raw_df = pd.DataFrame(raw_data)
    print(f"[Phase 1] Successfully fetched {len(raw_df)} stocks in {ingest_time:.2f}s.")

    # 2. Phase 2: Multi-Factor Scoring & Ranking
    print("\n[Phase 2] Computing Value, Quality, Growth percentile scores...")
    
    # Model Weights: Valuation (40%), Quality (30%), Growth (30%)
    ranked_df = calculate_quant_scores(
        raw_df,
        value_weight=0.4,
        quality_weight=0.3,
        growth_weight=0.3
    )

    # 3. Output Display
    display_cols = [
        "Rank", "Symbol", "Price", "Trailing P/E", "ROE", 
        "Valuation Score", "Quality Score", "Growth Score", "Quant Score"
    ]
    
    # Filter display to columns present in the DataFrame
    available_cols = [c for c in display_cols if c in ranked_df.columns]

    print("\n" + "=" * 80)
    print(" LEADERBOARD — TOP QUANT RANKED STOCKS ")
    print("=" * 80)
    print(ranked_df[available_cols].head(15).to_string(index=False))
    print("=" * 80)


if __name__ == "__main__":
    main()