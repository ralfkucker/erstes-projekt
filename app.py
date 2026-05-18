import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(layout="wide")

# ======================
# HEADER
# ======================
st.title("🚀 AI Trading Terminal PRO")

# ======================
# SIDEBAR
# ======================
st.sidebar.header("Settings")

ticker = st.sidebar.text_input("Ticker", "AAPL")
period = st.sidebar.selectbox("Zeitraum", ["6mo", "1y", "2y"])

# ======================
# DATA
# ======================
data = yf.download(ticker, period=period)

# Fehler abfangen, falls keine Daten
if data is None or data.empty:
    st.error("Keine Daten gefunden. Bitte anderen Ticker eingeben.")
    st.stop()

# ======================
# AI MARKET PHASE
# ======================
returns = data["Close"].pct_change()
volatility = returns.rolling(20).std()

# sichere Werte (keine NaNs!)
current_vol = volatility.dropna().iloc[-1]
avg_vol = volatility.dropna().mean()

if current_vol > avg_vol:
    regime = "🔴 Risk Off"
else:
    regime = "🟢 Risk On"

# ======================
# SIGNAL ENGINE
# ======================
ma_short = data["Close"].rolling(20).mean()
ma_long = data["Close"].rolling(50).mean()

ma_short_last = ma_short.dropna().iloc[-1]
ma_long_last = ma_long.dropna().iloc[-1]

if ma_short_last > ma_long_last:
    signal = "🟢 BUY"
    confidence = round((ma_short_last / ma_long_last - 1) * 100, 2)
else:
    signal = "🔴 SELL"
    confidence = round((ma_long_last / ma_short_last - 1) * 100, 2)

# ======================
# LAYOUT
# ======================
col1, col2, col3 = st.columns(3)

col1.metric("Market Phase", regime)
col2.metric("Signal", signal)
col3.metric("Confidence %", confidence)

# ======================
# CHARTS
# ======================
st.subheader("Price Chart")
st.line_chart(data["Close"])

st.subheader("Volatility")
st.line_chart(volatility)

# ======================
# OPTIONS ENGINE (BASIC)
# ======================
st.subheader("Options Strategy Engine")

if regime == "🟢 Risk On":
    strategy = "Bullish: Short Put / Bull Call Spread"
elif regime == "🔴 Risk Off":
    strategy = "Neutral/Defensive: Iron Condor / Short Call"
else:
    strategy = "Neutral: Strangle"

st.write("Empfohlene Strategie:", strategy)

# ======================
# ADVANCED STRATEGIES
# ======================
st.subheader("Advanced Strategies")

st.write("✔ Iron Condor")
st.write("✔ Long Strangle")
st.write("✔ Short Strangle")
st.write("✔ Risk Reversal")
st.write("✔ Collar")

# ======================
# DATA TABLE
# ======================
st.subheader("Latest Data")
st.dataframe(data.tail())
