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

# ======================
# AI MARKET PHASE
# ======================
returns = data["Close"].pct_change()
volatility = returns.rolling(20).std()

current_vol = float(volatility.iloc[-1])
avg_vol = float(volatility.mean())

if current_vol > avg_vol:
avg_vol = float(volatility.mean())

if current_vol > avg_vol:
    regime = "🔴 Risk Off"
else:
    regime = "🟢 Risk On"

# ======================
# SIGNAL ENGINE
# ======================
ma_short = data["Close"].rolling(20).mean()
ma_long = data["Close"].rolling(50).mean()

if ma_short.iloc[-1] > ma_long.iloc[-1]:
    signal = "🟢 BUY"
    confidence = round((ma_short.iloc[-1] / ma_long.iloc[-1] - 1) * 100, 2)
else:
    signal = "🔴 SELL"
    confidence = round((ma_long.iloc[-1] / ma_short.iloc[-1] - 1) * 100, 2)

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
    strategy = "Short Put / Bull Call Spread"
elif regime == "🔴 Risk Off":
    strategy = "Iron Condor / Short Call"
else:
    strategy = "Neutral Strangle"

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
