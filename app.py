import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime # ይህ መስመር ነው image_68572b.png ላይ ላለው ስህተት መፍትሄው
from streamlit_autorefresh import st_autorefresh

# --- 1. የቴሌግራም መረጃዎች ---
BOT_TOKEN = "8697770325:AAEBF1hdY69TwJo53thF7yzyhm9uWJaSsE0"
CHAT_ID = "8697770325"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url, timeout=5)
    except:
        pass

# --- 2. ገጽታ እና Auto-Refresh ---
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")

# በየ 60 ሰከንዱ ገጹን ራሱ እንዲያድስ ያደርገዋል
st_autorefresh(interval=60000, key="ticker_update")

st.title("🏹 ICT Smart Money AI (Live Refresh)")

# Sidebar
st.sidebar.header("Trading Settings")
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Select Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# --- 3. ዳታ ማውረድ ---
data = yf.download(ticker, period="3d", interval=timeframe)

if data.empty:
    st.error("ዳታ መጫን አልተቻለም!")
    st.stop()

# --- 4. ICT Logic (PDH/PDL) ---
df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()
df = df.dropna().copy()

# --- 5. ቻርቱን በ Plotly መስራት ---
fig = go.Figure(data=[go.Candlestick(
    x=df.iloc[:,0],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Price"
)])

last_signal_text = ""
for i in range(1, len(df)):
    current = df.iloc[i]
    prev = df.iloc[i-1]
    time_val = df.iloc[i, 0]
    
    if current['close'] > current['pdl'] and prev['low'] < current['pdl']:
        fig.add_annotation(x=time_val, y=current['low'], text="BUY",
                           showarrow=True, arrowhead=1, bgcolor="#26a69a", font=dict(color="white"))
        if i == len(df) - 1:
            last_signal_text = f"🚀 BUY SIGNAL: {ticker} @ {float(current['close']):,.5f}"
    
    elif current['close'] < current['pdh'] and prev['high'] > current['pdh']:
        fig.add_annotation(x=time_val, y=current['high'], text="SELL",
                           showarrow=True, arrowhead=1, bgcolor="#ef5350", font=dict(color="white"), ay=-40)
        if i == len(df) - 1:
            last_signal_text = f"⚠️ SELL SIGNAL: {ticker} @ {float(current['close']):,.5f}"

fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df['pdh'], name="PDH", line=dict(color='red', width=1, dash='dash')))
fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df['pdl'], name="PDL", line=dict(color='green', width=1, dash='dash')))

fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)

# --- 6. ማሳያ (UI) ---
col1, col2 = st.columns([4, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write(f"**Asset:** {ticker}")
    # እዚህ ጋር አሁን ስህተቱ አይመጣም
    st.write(f"**Last Update:** {datetime.now().strftime('%H:%M:%S')}")
    st.metric("Price", f"{float(df.iloc[-1]['close']):,.5f}")
    
    if last_signal_text:
        st.success("New Signal!")
        st.write(last_signal_text)
        send_telegram_msg(last_signal_text)
        st.balloons()
    else:
        st.info("Scanning Market...")
