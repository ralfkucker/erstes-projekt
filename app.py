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
period = st.sidebar.selectbox("Zeitraum", ["3mo", "6mo", "1y", "2y"])

# ======================
# DATA LOAD (SAFE)
# ======================
@st.cache_data
def load_data(ticker, period):
    try:
        data = yf.download(ticker, period=period)
        return data
    except:
        return pd.DataFrame()

data = load_data(ticker, period)

if data is None or data.empty or len(data) < 30:
    st.error("Nicht genug Daten verfügbar.")
    st.stop()

# sauber runden
data = data.round(2)

# ======================
# VOL ENGINE (ROBUST)
# ======================
returns = data["Close"].pct_change()

vol_daily = returns.rolling(20).std()
vol_annual = vol_daily * np.sqrt(252)

vol_clean = vol_annual.dropna()

if len(vol_clean) == 0:
    st.warning("Volatilität kann nicht berechnet werden.")
    st.stop()

current_vol = float(vol_clean.iloc[-1])
avg_vol = float(vol_clean.mean())

current_vol_pct = current_vol * 100
avg_vol_pct = avg_vol * 100

# ======================
# MARKET REGIME
# ======================
if current_vol > avg_vol:
    regime = "🔴 Risk Off"
else:
    regime = "🟢 Risk On"

# ======================
# OPTIONS ENGINE
# ======================
def get_strategy(regime, vol):
    if regime == "🟢 Risk On" and vol < 20:
        return "📈 Trend: Long Calls / Short Puts"
    elif regime == "🟢 Risk On" and vol >= 20:
        return "⚖️ Mixed: Call Spreads"
    elif regime == "🔴 Risk Off" and vol < 20:
        return "🛡️ Defensive: Protective Puts"
    else:
        return "💰 Income: Iron Condor / Short Strangle"

strategy = get_strategy(regime, current_vol_pct)

# ======================
# LAYOUT
# ======================
col1, col2 = st.columns([2, 1])

# ===== CHART FIXED
with col1:
    st.subheader("📊 Price Chart")

    # Auto Scaling Chart
    st.line_chart(data["Close"], use_container_width=True)

# ===== RIGHT PANEL
with col2:
    st.subheader("🧠 Market Regime")

    st.write(f"Aktuelle Volatilität: **{current_vol_pct:.2f}%**")
    st.write(f"Durchschnitt: **{avg_vol_pct:.2f}%**")
    st.write(f"Marktphase: {regime}")

    st.subheader("📊 Options Engine")
    st.info(strategy)

# ======================
# EXTRA: VOL CHART
# ======================
st.subheader("📉 Volatility (Annualized)")
st.line_chart(vol_annual.dropna(), use_container_width=True)

# ======================
# DATA TABLE
# ======================
with st.expander("📋 Rohdaten anzeigen"):
    st.dataframe(data.tail())
