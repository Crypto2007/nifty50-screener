import unittest
import numpy as np
import pandas as pd
from fetcher import load_universe
from quant import sanitize_data, calculate_quant_scores


class TestQuantScreener(unittest.TestCase):

    def setUp(self):
        """Set up mock raw financial data with edge cases."""
        self.mock_raw_data = pd.DataFrame([
            {
                "Symbol": "GOOD_STK.NS",
                "Price": 500.0,
                "Trailing P/E": 15.0,     # Value: Good
                "Price to Book": 2.0,      # Value: Good
                "ROE": 0.25,               # Quality: High (25%)
                "Profit Margin": 0.18,     # Quality: High (18%)
                "Revenue Growth": 0.20     # Growth: Strong (20%)
            },
            {
                "Symbol": "EXPNSV_STK.NS",
                "Price": 1200.0,
                "Trailing P/E": 80.0,     # Value: Poor
                "Price to Book": 12.0,     # Value: Poor
                "ROE": 0.30,               # Quality: High (30%)
                "Profit Margin": 0.22,     # Quality: High (22%)
                "Revenue Growth": 0.15     # Growth: Good (15%)
            },
            {
                "Symbol": "LOSS_MAKER.NS",
                "Price": 80.0,
                "Trailing P/E": -10.0,    # Negative P/E (Loss maker)
                "Price to Book": -1.5,     # Negative P/B
                "ROE": -0.05,              # Negative ROE
                "Profit Margin": -0.02,
                "Revenue Growth": -0.10
            },
            {
                "Symbol": "MISSING_DATA.NS",
                "Price": 250.0,
                "Trailing P/E": np.nan,    # Missing values
                "Price to Book": 3.0,
                "ROE": "N/A",              # String garbage
                "Profit Margin": 0.10,
                "Revenue Growth": np.inf   # Infinity edge case
            }
        ])

    def test_universe_loader(self):
        """Test Phase 1: Universe loader returns valid symbols."""
        tickers = load_universe("nifty_50")
        self.assertIsInstance(tickers, list)
        self.assertGreater(len(tickers), 0)
        self.assertTrue(all(isinstance(t, str) for t in tickers))

    def test_data_sanitization(self):
        """Test Phase 2: Edge-case sanitization rules."""
        sanitized = sanitize_data(self.mock_raw_data)

        # 1. Loss-makers (P/E <= 0) should be converted to NaN and imputed with positive median
        loss_maker_pe = sanitized.loc[sanitized["Symbol"] == "LOSS_MAKER.NS", "Trailing P/E"].values[0]
        self.assertFalse(pd.isna(loss_maker_pe))
        self.assertGreater(loss_maker_pe, 0.0)

        # 2. Infinite values replaced with NaN then median imputed
        missing_growth = sanitized.loc[sanitized["Symbol"] == "MISSING_DATA.NS", "Revenue Growth"].values[0]
        self.assertFalse(np.isinf(missing_growth))
        self.assertFalse(pd.isna(missing_growth))

        # 3. Non-numeric strings coerced without crashing
        missing_roe = sanitized.loc[sanitized["Symbol"] == "MISSING_DATA.NS", "ROE"].values[0]
        self.assertFalse(pd.isna(missing_roe))

    def test_quant_scoring_and_ranking(self):
        """Test Phase 2: Scoring calculations and auto-ranking."""
        ranked_df = calculate_quant_scores(
            self.mock_raw_data,
            value_weight=0.4,
            quality_weight=0.3,
            growth_weight=0.3
        )

        # 1. Check required output columns presence
        expected_cols = [
            "Rank", "Valuation Score", "Quality Score", 
            "Growth Score", "Quant Score"
        ]
        for col in expected_cols:
            self.assertIn(col, ranked_df.columns)

        # 2. Check Rank column starting index and ordering
        self.assertEqual(ranked_df["Rank"].iloc[0], 1)

        # 3. Check Quant Score monotonicity (sorted descending)
        scores = ranked_df["Quant Score"].tolist()
        self.assertEqual(scores, sorted(scores, reverse=True))

        # 4. Check percentile bounds (0 to 100)
        for col in ["Valuation Score", "Quality Score", "Growth Score", "Quant Score"]:
            self.assertTrue((ranked_df[col] >= 0.0).all() and (ranked_df[col] <= 100.0).all())


if __name__ == "__main__":
    unittest.main(verbosity=2)