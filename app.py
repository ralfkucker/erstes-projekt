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

if data is None or data.empty:
    st.error("Keine Daten gefunden.")
    st.stop()

# Preise sauber runden
data = data.round(2)

# ======================
# VOL ENGINE (PRO)
# ======================
returns = data["Close"].pct_change()

vol_daily = returns.rolling(20).std()
vol_annual = vol_daily * np.sqrt(252)

vol_clean = vol_annual.dropna()

current_vol = float(vol_clean.iloc[-1])
avg_vol = float(vol_clean.mean())

current_vol_pct = current_vol * 100
avg_vol_pct = avg_vol * 100

# ======================
# MARKET REGIME
# ======================
if current_vol > avg_vol:
    regime = "Risk Off"
else:
    regime = "Risk On"

# ======================
# OPTIONS ENGINE
# ======================
st.subheader("🧠 Market Regime")

st.write(f"Aktuelle Volatilität: {current_vol_pct:.2f}%")
st.write(f"Durchschnitt: {avg_vol_pct:.2f}%")
st.write(f"Marktphase: {'🟢' if regime=='Risk On' else '🔴'} {regime}")

st.subheader("📊 Options Engine")

if regime == "Risk On":
    st.success("➡️ Trend-Strategien")

    st.markdown("""
    - Long Calls  
    - Short Puts  
    - Trend Following  
    """)
else:
    st.warning("➡️ Volatilitäts-Strategien")

    st.markdown("""
    - Iron Condor  
    - Short Strangle  
    - Credit Spreads  
    """)

# ======================
# CHART (FIXED)
# ======================
st.subheader("📈 Price Chart")

chart_data = data["Close"]

# Auto Scale fix (kein Nullstart)
y_min = float(chart_data.min()) * 0.95
y_max = float(chart_data.max()) * 1.05

st.line_chart(chart_data)

# ======================
# DATA TABLE
# ======================
with st.expander("📋 Rohdaten anzeigen"):
    st.dataframe(data.tail(50))
