import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.linear_model import LogisticRegression
from scipy.stats import norm

st.set_page_config(layout="wide")
st.title("🚀 AI Trading Terminal – FUND DASHBOARD PRO (FINAL)")

# =========================
# SETTINGS
# =========================
st.sidebar.header("⚙️ Settings")

tickers = st.sidebar.text_input("Watchlist", "SPY,QQQ,GLD,TLT").split(",")
capital = st.sidebar.number_input("Kapital (€)", value=100000)

st.sidebar.subheader("🎛️ Factor Weights")

w_trend = st.sidebar.slider("Trend", 0, 100, 20)
w_mom = st.sidebar.slider("Momentum", 0, 100, 15)
w_vol = st.sidebar.slider("Volatility", 0, 100, 15)
w_macro = st.sidebar.slider("Macro", 0, 100, 15)
w_corr = st.sidebar.slider("Correlation", 0, 100, 10)
w_flow = st.sidebar.slider("Flow", 0, 100, 15)

weights = np.array([w_trend, w_mom, w_vol, w_macro, w_corr, w_flow])
weights = weights / weights.sum()

# =========================
# DATA
# =========================
def load_data(ticker):
    df = yf.download(ticker, period="1y")
    return df.dropna()

# =========================
# FEATURE ENGINEERING
# =========================
def create_features(df):
    df["returns"] = df["Close"].pct_change()
    df["ma50"] = df["Close"].rolling(50).mean()
    df["ma200"] = df["Close"].rolling(200).mean()
    df["vol"] = df["returns"].rolling(20).std()

    df["trend"] = df["Close"] - df["ma50"]
    df["momentum"] = df["returns"].rolling(10).mean()

    df = df.dropna()

    X = df[["trend", "momentum", "vol"]]
    y = (df["returns"].shift(-1) > 0).astype(int)

    return X[:-1], y[:-1], df

# =========================
# ML MODEL
# =========================
def train_ml(X, y):
    model = LogisticRegression()
    model.fit(X, y)
    return model

# =========================
# SCORE
# =========================
def calc_score(df):
    trend = 1 if df["Close"].iloc[-1] > df["ma50"].iloc[-1] else -1
    mom = 1 if df["momentum"].iloc[-1] > 0 else -1
    vol = -1 if df["vol"].iloc[-1] > df["vol"].mean() else 1

    macro = 0
    corr = 0
    flow = 0

    factors = np.array([trend, mom, vol, macro, corr, flow])
    return np.dot(weights, factors) * 100

# =========================
# BACKTEST
# =========================
def backtest(df):
    cash = 10000
    position = 0
    equity = []

    for i in range(50, len(df)-1):
        price = df["Close"].iloc[i]

        if df["momentum"].iloc[i] > 0:
            position = cash / price
            cash = 0
        else:
            cash = position * price
            position = 0

        equity.append(cash + position * price)

    return equity

# =========================
# MONTE CARLO
# =========================
def monte_carlo(returns, sims=200):
    results = []

    for _ in range(sims):
        sim = np.random.choice(returns, size=len(returns))
        path = np.cumprod(1 + sim)
        results.append(path[-1])

    return np.percentile(results, [5,50,95])

# =========================
# MAIN
# =========================
results = []

for t in tickers:
    data = load_data(t.strip())
    if data.empty:
        continue

    X, y, df = create_features(data)
    model = train_ml(X, y)

    latest = X.iloc[-1].values.reshape(1,-1)
    prob = model.predict_proba(latest)[0][1]

    score = calc_score(df)

    final_score = 0.7 * score + 0.3 * (prob * 100)

    equity = backtest(df)

    mc = monte_carlo(df["returns"].dropna())

    results.append({
        "Ticker": t,
        "Score": round(final_score,2),
        "ML Prob ↑": round(prob*100,2),
        "MonteCarlo Worst": round(mc[0],2),
        "MonteCarlo Median": round(mc[1],2),
        "MonteCarlo Best": round(mc[2],2)
    })

df_res = pd.DataFrame(results)

# =========================
# DASHBOARD
# =========================
st.subheader("📊 Signal Board")
st.dataframe(df_res)

# =========================
# CHART
# =========================
ticker = st.selectbox("Chart", df_res["Ticker"])

data = load_data(ticker)

fig = go.Figure()
fig.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Price"))
st.plotly_chart(fig, use_container_width=True)

# =========================
# BACKTEST CHART
# =========================
st.subheader("📈 Backtest")

X, y, df = create_features(data)
equity = backtest(df)

fig2 = go.Figure()
fig2.add_trace(go.Scatter(y=equity, name="Equity"))
st.plotly_chart(fig2, use_container_width=True)

# =========================
# OPTIONS ENGINE
# =========================
st.subheader("📊 Options Engine")

S = data["Close"].iloc[-1]
K = st.number_input("Strike", value=float(round(S)))
T = st.slider("Years", 0.1, 2.0, 0.5)
r = 0.02
sigma = 0.2

def bs_call(S,K,T,r,sigma):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    return S*norm.cdf(d1)-K*np.exp(-r*T)*norm.cdf(d2)

def bs_put(S,K,T,r,sigma):
    d1=(np.log(S/K)+(r+sigma**2/2)*T)/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    return K*np.exp(-r*T)*norm.cdf(-d2)-S*norm.cdf(-d1)

st.write("Call:", round(bs_call(S,K,T,r,sigma),2))
st.write("Put:", round(bs_put(S,K,T,r,sigma),2))
