import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

st.set_page_config(page_title="AI Fund Dashboard", layout="wide")

st.title("🚀 AI Fund Dashboard PRO")

ticker = st.text_input("Asset (z.B. AAPL, TSLA, SPY)", "AAPL")

data = yf.download(ticker, period="3mo", interval="1d")

if not data.empty:
    st.line_chart(data["Close"])

    returns = data["Close"].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)

    st.metric("Volatility (annualized)", f"{vol:.2%}")

    if vol > 0.4:
        regime = "🔥 High Vol / Risk"
    elif vol > 0.2:
        regime = "⚖️ Neutral"
    else:
        regime = "🟢 Low Risk"

    st.subheader(f"Market Regime: {regime}")

else:
    st.error("Keine Daten gefunden")
