import streamlit as st
import yfinance as yf
import pandas as pd
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
st.set_page_config(page_title="ICT Pro Terminal", layout="wide")
st_autorefresh(interval=60000, key="live_update") # በየደቂቃው ራሱን ያድሳል

st.title("🏹 ICT Advanced Strategy Terminal")

# Sidebar
ticker = st.sidebar.selectbox("Asset", ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"])

# --- 3. ዳታ ማውረድ ---
data = yf.download(ticker, period="3d", interval=timeframe)
if data.empty: st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# --- 4. ICT Advanced Logic ---
# Equilibrium & OTE (ለቻርቱ ብቻ)
high_3d = df['high'].max()
low_3d = df['low'].min()
equilibrium = (high_3d + low_3d) / 2
ote_deep = low_3d + (high_3d - low_3d) * 0.79
ote_shallow = low_3d + (high_3d - low_3d) * 0.62

# FVG Detection
def get_fvgs(df):
    fvgs = []
    for i in range(2, len(df)):
        if df.iloc[i-2]['high'] < df.iloc[i]['low']: # Bullish
            fvgs.append({'type': 'Bullish', 'top': df.iloc[i]['low'], 'bottom': df.iloc[i-2]['high']})
        elif df.iloc[i-2]['low'] > df.iloc[i]['high']: # Bearish
            fvgs.append({'type': 'Bearish', 'top': df.iloc[i-2]['low'], 'bottom': df.iloc[i]['high']})
    return fvgs

# Order Block Detection (OB)
def get_obs(df):
    obs = []
    for i in range(1, len(df)-1):
        if df.iloc[i+1]['close'] > df.iloc[i]['high'] and df.iloc[i]['close'] < df.iloc[i]['open']:
            obs.append({'type': 'Bullish', 'level': df.iloc[i]['high']})
        elif df.iloc[i+1]['close'] < df.iloc[i]['low'] and df.iloc[i]['close'] > df.iloc[i]['open']:
            obs.append({'type': 'Bearish', 'level': df.iloc[i]['low']})
    return obs

current_fvgs = get_fvgs(df)
current_obs = get_obs(df)
curr_price = df.iloc[-1]['close']

# --- 5. ሲግናል መላኪያ (OB ወይም FVG ሲነካ ብቻ) ---
entry_triggered = False
msg_content = ""

# የቅርብ ጊዜ OB መነካቱን ቼክ ማድረግ
for ob in current_obs[-2:]:
    if abs(curr_price - ob['level']) / ob['level'] < 0.0005: # ዋጋው OB ጋር ሲጠጋ
        entry_triggered = True
        msg_content = f"🎯 ICT ENTRY: {ticker}\nPrice hit an ORDER BLOCK at {curr_price:,.2f}!"

# የቅርብ ጊዜ FVG መነካቱን ቼክ ማድረግ
for fvg in current_fvgs[-2:]:
    if fvg['bottom'] <= curr_price <= fvg['top']:
        entry_triggered = True
        msg_content = f"🎯 ICT ENTRY: {ticker}\nPrice entered a FAIR VALUE GAP at {curr_price:,.2f}!"

if entry_triggered:
    send_telegram_msg(msg_content)

# --- 6. ቻርቱን መስራት (ሁሉም ምስሉ ላይ ያሉ ነገሮች አሉ) ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="Price")])
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

# OB መስመሮችን ማሳያ
for ob in current_obs[-3:]:
    fig.add_hline(y=ob['level'], line_color="cyan", line_width=1, opacity=0.4)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

# --- 7. UI ማሳያ ---
c1, c2 = st.columns([3, 1])
with c1: st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Market Status")
    if st.button("📢 ቴሌግራምን ሞክር"):
        send_telegram_msg("🚀 ቦቱ በትክክል እየሰራ ነው። OB ወይም FVG ሲነካ መልዕክት ይልክልሃል።")
    
    st.metric("Current Price", f"{curr_price:,.2f}")
    st.divider()
    if entry_triggered:
        st.success("🔥 ENTRY DETECTED!")
    else:
        st.info("Market Scanning for OB/FVG...")
    st.write(f"🕒 Sync: {datetime.now().strftime('%H:%M:%S')}")
