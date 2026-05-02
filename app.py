import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. የተስተካከለ የቴሌግራም መረጃ ---
BOT_TOKEN = "8697770325:AAEBF1hdY69TwJo53thF7yzyhm9uWJaSsE0"
CHAT_ID = "8125084772" # ያንተ ትክክለኛ ID እዚህ ገብቷል

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url, timeout=5)
    except:
        pass

# --- 2. ገጽታ እና Auto-Refresh ---
st.set_page_config(page_title="ICT AI Terminal", layout="wide")
st_autorefresh(interval=60000, key="live_update")

st.title("🏹 ICT Smart Money AI Pro")

# Sidebar
st.sidebar.header("Trading Terminal")
ticker = st.sidebar.selectbox("Asset", ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"])

# --- 3. ዳታ እና ስልት (ICT Logic) ---
data = yf.download(ticker, period="3d", interval=timeframe)
if data.empty: st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# PDH/PDL
df['pdh'] = df['high'].shift(1).rolling(window=24).max()
df['pdl'] = df['low'].shift(1).rolling(window=24).min()

# FVG Detection
def find_fvg(df):
    fvgs = []
    for i in range(2, len(df)):
        if df.iloc[i-2]['high'] < df.iloc[i]['low']:
            fvgs.append({'type': 'Bullish', 'top': df.iloc[i]['low'], 'bottom': df.iloc[i-2]['high'], 'index': i-1})
        elif df.iloc[i-2]['low'] > df.iloc[i]['high']:
            fvgs.append({'type': 'Bearish', 'top': df.iloc[i-2]['low'], 'bottom': df.iloc[i]['high'], 'index': i-1})
    return fvgs

fvgs = find_fvg(df)

# --- 4. ቻርቱን መስራት ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Market")])

# FVG ሳጥኖች
for f in fvgs[-5:]:
    color = "rgba(0, 255, 0, 0.2)" if f['type'] == 'Bullish' else "rgba(255, 0, 0, 0.2)"
    fig.add_shape(type="rect", x0=df.iloc[f['index'], 0], y0=f['bottom'], x1=df.iloc[-1, 0], y1=f['top'], fillcolor=color, line_width=0)

# ሲግናል መፈለጊያ
last_row = df.iloc[-1]
prev_row = df.iloc[-2]
signal = None

if last_row['close'] > last_row['pdl'] and prev_row['low'] < last_row['pdl']:
    signal = "BUY"
    price, sl = float(last_row['close']), float(last_row['pdl'] * 0.999)
    tp = float(price + (price - sl) * 2)
elif last_row['close'] < last_row['pdh'] and prev_row['high'] > last_row['pdh']:
    signal = "SELL"
    price, sl = float(last_row['close']), float(last_row['pdh'] * 1.001)
    tp = float(price - (sl - price) * 2)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

# --- 5. UI እና ውጤት ማሳያ ---
c1, c2 = st.columns([3, 1])
with c1: st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Signal Details")
    if st.button("ቴሌግራምን ሞክር"):
        send_telegram_msg("🚀 የቴሌግራም ቦቱ አሁን በትክክል ተገናኝቷል!")
        st.success("ሙከራ ተልኳል!")
    
    if signal:
        st.markdown(f"### 🔥 {signal} SIGNAL")
        st.write(f"**Entry:** {price:,.5f}\n**SL:** {sl:,.5f}\n**TP:** {tp:,.5f}")
        send_telegram_msg(f"🎯 {signal} SIGNAL: {ticker}\nEntry: {price:,.5f}\nSL: {sl:,.5f}\nTP: {tp:,.5f}")
    else:
        st.info("Scanning Market...")
    
    st.write(f"🕒 Last Sync: {datetime.now().strftime('%H:%M:%S')}")
