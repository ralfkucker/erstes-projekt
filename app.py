# app.py

from fastapi import FastAPI, WebSocket
import asyncio
import random
from datetime import datetime

app = FastAPI()

# ==============================
# CONFIG
# ==============================

CONFIDENCE_THRESHOLD = 0.75
MAX_DAILY_LOSS = -5000

# ==============================
# STATE
# ==============================

clients = []

portfolio = {
    "cash": 100000,
    "positions": [],
    "pnl": 0
}

trade_log_file = "trades.log"

# ==============================
# UTILS
# ==============================

def log_trade(signal, pnl):
    entry = {
        "time": str(datetime.now()),
        "symbol": signal["symbol"],
        "action": signal["action"],
        "confidence": signal["confidence"],
        "pnl": pnl
    }

    with open(trade_log_file, "a") as f:
        f.write(str(entry) + "\n")


def kill_switch():
    return portfolio["pnl"] > MAX_DAILY_LOSS


def execute_trade(signal):

    position = {
        "symbol": signal["symbol"],
        "entry": random.uniform(90, 110),
        "size": 1
    }

    portfolio["positions"].append(position)

    return position


def update_pnl():

    total = 0

    for pos in portfolio["positions"]:
        current_price = random.uniform(90, 110)
        pnl = (current_price - pos["entry"]) * pos["size"]
        total += pnl

    portfolio["pnl"] = total
    return total


# ==============================
# AI SIGNAL GENERATOR (placeholder)
# ==============================

def generate_signal():

    return {
        "symbol": random.choice(["AAPL", "TSLA", "BTC", "NVDA"]),
        "action": random.choice(["BUY", "SELL"]),
        "confidence": round(random.uniform(0.6, 0.95), 2),
        "explain": {
            "lstm": random.choice(["bullish", "bearish"]),
            "transformer": "trend",
            "macro": random.choice(["risk-on", "risk-off"]),
            "orderbook": random.choice(["buy pressure", "sell pressure"])
        }
    }


# ==============================
# MAIN WEBSOCKET
# ==============================

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):

    await ws.accept()
    clients.append(ws)

    try:
        while True:

            # Kill Switch Check
            if not kill_switch():
                await ws.send_json({"error": "KILL SWITCH ACTIVATED"})
                break

            signal = generate_signal()

            executed = False
            trade_result = None

            # ==============================
            # 🔥 CONFIDENCE FILTER
            # ==============================

            if signal["confidence"] >= CONFIDENCE_THRESHOLD:
                trade = execute_trade(signal)
                executed = True
                trade_result = trade

            # Update PnL
            pnl = update_pnl()

            # Log Trade (nur wenn ausgeführt)
            if executed:
                log_trade(signal, pnl)

            # Send to frontend
            data = {
                "portfolio": portfolio["cash"] + pnl,
                "pnl": pnl,
                "signal": signal,
                "executed": executed,
                "positions": len(portfolio["positions"])
            }

            await ws.send_json(data)

            await asyncio.sleep(1)

    except Exception as e:
        print("Connection closed:", e)
        clients.remove(ws)
