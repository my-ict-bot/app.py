import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. የቴሌግራም መረጃ ---
BOT_TOKEN = "8697770325:AAEBF1hdY69TwJo53thF7yzyhm9uWJaSsE0"
CHAT_ID = "8125084772"

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID}&text={message}"
    try: requests.get(url, timeout=5)
    except: pass

# --- 2. ገጽታ ---
st.set_page_config(page_title="ICT Advanced AI", layout="wide")
st_autorefresh(interval=60000, key="live_update")

st.title("🏹 ICT Advanced Strategy Terminal")

# Sidebar
st.sidebar.header("Advanced Settings")
ticker = st.sidebar.selectbox("Asset", ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"])

# --- 3. ዳታ ማውረድ ---
data = yf.download(ticker, period="3d", interval=timeframe)
if data.empty: st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# --- 4. ICT Advanced Logic ---

# Equilibrium & OTE (Fibonacci)
high_3d = df['high'].max()
low_3d = df['low'].min()
equilibrium = (high_3d + low_3d) / 2
ote_deep = low_3d + (high_3d - low_3d) * 0.79
ote_shallow = low_3d + (high_3d - low_3d) * 0.62

# Order Block (ቀላል Logic)
def detect_ob(df):
    obs = []
    for i in range(1, len(df)-1):
        # Bullish OB (መጨረሻ የነበረች ቀይ ሻማ ከኃይለኛ አረንጓዴ በፊት)
        if df.iloc[i]['close'] < df.iloc[i]['open'] and df.iloc[i+1]['close'] > df.iloc[i]['high']:
            obs.append({'type': 'Bullish', 'price': df.iloc[i]['close'], 'time': df.iloc[i,0]})
        # Bearish OB
        elif df.iloc[i]['close'] > df.iloc[i]['open'] and df.iloc[i+1]['close'] < df.iloc[i]['low']:
            obs.append({'type': 'Bearish', 'price': df.iloc[i]['close'], 'time': df.iloc[i,0]})
    return obs

obs = detect_ob(df)

# Price Delivery Phase
last_pct_change = ((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]) * 100
if abs(last_pct_change) < 0.1: phase = "Consolidation 🛡️"
elif last_pct_change > 0.3: phase = "Expansion (Bullish) 🚀"
elif last_pct_change < -0.3: phase = "Expansion (Bearish) 📉"
else: phase = "Retracement/Reversal 🔄"

# --- 5. ቻርቱን መስራት ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])

# Equilibrium Line
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium (50%)")

# OTE Zone
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

# Order Blocks (ቅርብ ጊዜ የነበሩትን)
for ob in obs[-3:]:
    color = "green" if ob['type'] == 'Bullish' else "red"
    fig.add_hline(y=ob['price'], line_color=color, line_width=1, opacity=0.5)

fig.update_layout(template="plotly_dark", height=650, xaxis_rangeslider_visible=False)

# --- 6. UI ማሳያ ---
col1, col2 = st.columns([4, 1])

with col1:
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Market Status")
    st.info(f"Phase: **{phase}**")
    
    st.metric("Current Price", f"{df.iloc[-1]['close']:,.2f}")
    
    st.divider()
    st.write("### Strategy Check")
    is_in_ote = ote_shallow <= df.iloc[-1]['close'] <= ote_deep
    st.write(f"In OTE Zone: {'✅' if is_in_ote else '❌'}")
    
    # ሲግናል መላኪያ
    if is_in_ote:
        st.success("🎯 OTE Setup Detected!")
        send_telegram_msg(f"🏹 ICT ALERT: {ticker} in OTE Zone!\nPhase: {phase}\nPrice: {df.iloc[-1]['close']:,.2f}")

    st.write(f"🕒 Sync: {datetime.now().strftime('%H:%M:%S')}")
