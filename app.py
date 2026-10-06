import logging
import streamlit as st
import pandas as pd
import plotly.express as px

import database as db
import fetcher
import quant

# Page Configuration
st.set_page_config(
    page_title="Nifty 50 Quantitative Equity Screener",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

logging.basicConfig(level=logging.INFO)


def _bootstrap_db() -> bool:
    """Ensure database schema is ready."""
    return db.init_db()


@st.cache_data(ttl=3600)
def load_and_score_data(val_weight: float, qual_weight: float, gro_weight: float) -> pd.DataFrame:
    """Loads stock cache (or fetches fresh data) and applies factor scoring."""
    df = db.load_stock_cache()
    if df.empty:
        with st.spinner("Fetching Nifty 50 market data from NSE via yfinance..."):
            df = fetcher.fetch_universe_data()
            db.save_stock_cache(df)

    weights = {"value": val_weight, "quality": qual_weight, "growth": gro_weight}
    scored_df = quant.calculate_quant_scores(df, weights)
    return scored_df


def main():
    _bootstrap_db()

    st.title("📈 Nifty 50 Quantitative Equity Screener")
    st.caption("Multi-Factor Factor Ranking Engine (Value, Quality, Growth)")

    # Sidebar Factor Weighting Controls
    st.sidebar.header("⚖️ Factor Model Weights")
    value_w = st.sidebar.slider("Value Weight (PE, PB, FCF Yield)", 0.0, 1.0, 0.35, 0.05)
    quality_w = st.sidebar.slider("Quality Weight (ROE, Margins, Debt)", 0.0, 1.0, 0.35, 0.05)
    growth_w = st.sidebar.slider("Growth Weight (Rev & EPS Growth)", 0.0, 1.0, 0.30, 0.05)

    if st.sidebar.button("🔄 Force Refresh Market Data"):
        st.cache_data.clear()
        with st.spinner("Re-fetching Nifty 50 universe data..."):
            fresh_df = fetcher.fetch_universe_data()
            db.save_stock_cache(fresh_df)
        st.sidebar.success("Nifty 50 market data updated successfully!")
        st.rerun()

    # Load and score dataset
    data = load_and_score_data(value_w, quality_w, growth_w)

    if data.empty:
        st.warning("No market data available. Please click 'Force Refresh Market Data' in the sidebar.")
        return

    # Top KPI Metrics Cards
    st.subheader("🏆 Top Ranked Quant Picks")
    top_3 = data.head(3)
    cols = st.columns(3)
    for idx, (_, row) in enumerate(top_3.iterrows()):
        with cols[idx]:
            st.metric(
                label=f"#{row['rank']} {row['ticker']}",
                value=f"{row['overall_percentile']:.1f} Score",
                delta=f"Price: ₹{row.get('current_price', 0.0):,.2f}" if pd.notnull(row.get('current_price')) else "N/A"
            )
            st.caption(f"{row.get('company_name', 'N/A')} | {row.get('sector', 'N/A')}")

    st.markdown("---")

    # Main Data Table & Visualizations
    tab1, tab2, tab3 = st.tabs(["📊 Screener Table", "🎯 Factor Scatter Plot", "🔍 Ticker Deep-Dive"])

    with tab1:
        st.subheader("Complete Nifty 50 Universe Ranking")
        
        # Sector Filter
        sectors = ["All"] + sorted(list(data["sector"].dropna().unique()))
        selected_sector = st.selectbox("Filter by Sector", sectors)
        
        filtered_df = data if selected_sector == "All" else data[data["sector"] == selected_sector]

        display_cols = [
            "rank", "ticker", "company_name", "sector", "overall_percentile",
            "value_score", "quality_score", "growth_score", "pe_ratio", "roe", "current_price"
        ]
        available_cols = [c for c in display_cols if c in filtered_df.columns]

        st.dataframe(
            filtered_df[available_cols].style.format({
                "overall_percentile": "{:.1f}",
                "value_score": "{:.2f}",
                "quality_score": "{:.2f}",
                "growth_score": "{:.2f}",
                "pe_ratio": "{:.1f}",
                "roe": "{:.1%}",
                "current_price": "₹{:,.2f}"
            }),
            use_container_width=True,
            height=400
        )

    with tab2:
        st.subheader("Value vs Quality Factor Matrix")
        fig = px.scatter(
            data,
            x="value_score",
            y="quality_score",
            size="overall_percentile",
            color="sector",
            hover_name="ticker",
            text="ticker",
            labels={"value_score": "Value Score (Z-Score)", "quality_score": "Quality Score (Z-Score)"},
            title="Factor Distribution Matrix (Bubble size = Overall Rank Percentile)"
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Stock Deep-Dive Analysis")
        selected_ticker = st.selectbox("Select a Ticker", data["ticker"].unique())
        ticker_data = data[data["ticker"] == selected_ticker].iloc[0]

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown(f"### **{ticker_data['company_name']} ({ticker_data['ticker']})**")
            st.write(f"**Sector:** {ticker_data.get('sector', 'N/A')}")
            st.write(f"**Industry:** {ticker_data.get('industry', 'N/A')}")
            st.write(f"**Current Price:** ₹{ticker_data.get('current_price', 0.0):,.2f}")
            st.write(f"**P/E Ratio:** {ticker_data.get('pe_ratio', 'N/A')}")
            st.write(f"**P/B Ratio:** {ticker_data.get('pb_ratio', 'N/A')}")

        with d_col2:
            st.markdown("### **Factor Scores**")
            st.write(f"**Value Z-Score:** {ticker_data.get('value_score', 0):.2f}")
            st.write(f"**Quality Z-Score:** {ticker_data.get('quality_score', 0):.2f}")
            st.write(f"**Growth Z-Score:** {ticker_data.get('growth_score', 0):.2f}")
            st.write(f"**Overall Percentile:** {ticker_data.get('overall_percentile', 0):.1f}%")


if __name__ == "__main__":
    main()