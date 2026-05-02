import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

# 1. የቴሌግራም መረጃዎች (ካንተ የተወሰዱ)
BOT_TOKEN = "8697770325:AAEBF1hdY69TwJo53thF7yzyhm9uWJaSsE0"
CHAT_ID = "8697770325"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try:
        requests.get(url, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# 2. ገጽታ (UI)
st.set_page_config(page_title="ICT Smart Money AI", layout="wide")
st.title("🏹 ICT Smart Money AI + Telegram Alert")

# Sidebar - ምርጫዎች
st.sidebar.header("Settings")
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "^GSPC"]
ticker = st.sidebar.selectbox("Select Asset", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "30m", "1h", "1d"])

# 3. ዳታ ማውረድ
@st.cache_data(ttl=60) # ዳታውን በየደቂቃው እንዲያድስ
def get_data(symbol, tf):
    df = yf.download(symbol, period="5d", interval=tf)
    return df

data = get_data(ticker, timeframe)

if data.empty:
    st.error("ዳታ አልተገኘም! እባክህ ኢንተርኔትህን ወይም ምልክቱን (Ticker) አረጋግጥ።")
    st.stop()

# 4. ዳታ ማጽዳት እና ICT Logic
df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# PDH (Previous Day High) እና PDL (Previous Day Low)
df['pdh'] = df['high'].shift(1).rolling(window=24, min_periods=1).max()
df['pdl'] = df['low'].shift(1).rolling(window=24, min_periods=1).min()
df = df.dropna().copy()

# 5. ቻርቱን በ Plotly መስራት
fig = go.Figure(data=[go.Candlestick(
    x=df['datetime'] if 'datetime' in df.columns else df['date'],
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name="Price"
)])

# Buy/Sell ሲግናሎችን መፈለግ እና ማሳየት
last_signal = ""
for i in range(1, len(df)):
    current = df.iloc[i]
    prev = df.iloc[i-1]
    time = current['datetime'] if 'datetime' in df.columns else current['date']
    
    # Buy Signal (Liquidity Sweep of PDL)
    if current['close'] > current['pdl'] and prev['low'] < current['pdl']:
        fig.add_annotation(x=time, y=current['low'], text="BUY",
                           showarrow=True, arrowhead=1, bgcolor="#26a69a", font=dict(color="white"))
        if i == len(df) - 1: # አሁን ለተፈጠረው ብቻ
            last_signal = f"🚀 ICT BUY SIGNAL: {ticker} at {float(current['close']):,.5f}"
    
    # Sell Signal (Liquidity Sweep of PDH)
    elif current['close'] < current['pdh'] and prev['high'] > current['pdh']:
        fig.add_annotation(x=time, y=current['high'], text="SELL",
                           showarrow=True, arrowhead=1, bgcolor="#ef5350", font=dict(color="white"), ay=-40)
        if i == len(df) - 1:
            last_signal = f"⚠️ ICT SELL SIGNAL: {ticker} at {float(current['close']):,.5f}"

# PDH/PDL መስመሮች
fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df['pdh'], name="PDH", line=dict(color='rgba(255, 0, 0, 0.4)', width=1, dash='dash')))
fig.add_trace(go.Scatter(x=df.iloc[:,0], y=df['pdl'], name="PDL", line=dict(color='rgba(0, 255, 0, 0.4)', width=1, dash='dash')))

fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)

# 6. ውጤቱን ማሳየት
col1, col2 = st.columns([4, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    curr_price = float(df.iloc[-1]['close'])
    st.metric("Current Price", f"{curr_price:,.5f}")
    
    if last_signal != "":
        st.success("Signal Detected!")
        st.write(last_signal)
        # ቴሌግራም መልዕክት ይላካል
        send_telegram_msg(last_signal)
        st.balloons()
    else:
        st.info("Scanning for ICT Setup...")

    st.write(f"**PDH:** {float(df.iloc[-1]['pdh']):,.5f}")
    st.write(f"**PDL:** {float(df.iloc[-1]['pdl']):,.5f}")
