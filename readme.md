# 📈 Nifty 50 Quantitative Equity Screener

A multi-factor quantitative equity research engine built with **Python**, **Streamlit**, **yfinance**, and **SQLite**. 

This application fetches fundamental financial metrics for all Nifty 50 constituents from the National Stock Exchange (NSE), normalizes metrics using **Z-score standardisation and Winsorization**, and ranks companies based on customizable factor weights.

---

## 🌟 Key Features

- **Live NSE Market Data:** Multithreaded parallel fetching of fundamental financial metrics via `yfinance`.
- **Multi-Factor Quant Model:**
  - **Value Factor:** P/E Ratio, P/B Ratio, Free Cash Flow Yield
  - **Quality Factor:** Return on Equity (ROE), Operating Margin, Debt-to-Equity
  - **Growth Factor:** Revenue Growth, EPS Growth
- **Statistical Normalization:** Outlier clipping (Winsorization) and Z-score standardization.
- **Interactive UI:**
  - Real-time factor weight customization sliders.
  - Sector filtering and data table sorting.
  - Plotly Value vs. Quality factor scatter matrix.
  - Individual ticker deep-dive analysis.
- **Caching Layer:** Local SQLite database persistence for lightning-fast loads.

---

## 🏗️ Project Architecture

```text
├── app.py              # Main Streamlit UI dashboard
├── quant.py            # Quantitative factor calculation & Z-scoring engine
├── fetcher.py          # Multithreaded yfinance NSE data fetcher
├── database.py         # SQLite database management & caching layer
├── requirements.txt    # Production dependencies
├── .gitignore          # Git ignore file
└── .streamlit/
    └── config.toml     # Streamlit theme & server configuration