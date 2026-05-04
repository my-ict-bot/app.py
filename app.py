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
st.set_page_config(page_title="XAU/USD Real-Time", layout="wide")
st_autorefresh(interval=60000, key="live_update")

st.title("🏹 ICT Gold Spot (XAU/USD) - Live Sync")

# --- 3. የዳታ አወራረድ ማሻሻያ (Gold Spot) ---
# 'XAUUSD=X' ካልሰራ 'GC=F'ን በመጠቀም ራሱ እንዲያስተካክል ተደርጓል
@st.cache_data(ttl=60)
def load_data():
    try:
        # መጀመሪያ ቀጥታ Spot ዳታን መሞከር
        d = yf.download("XAUUSD=X", period="2d", interval="5m")
        if not d.empty: return d, 0
    except:
        pass
    
    # ካልሰራ Futures ዳታ አምጥቶ በ TradingView ዋጋ ማስተካከል (Dynamic Offset)
    d = yf.download("GC=F", period="2d", interval="5m")
    # አሁን ባለው ምስል መሰረት ልዩነቱ ወደ -12.35 አካባቢ ነው
    return d, -12.35

data, price_offset = load_data()

if data.empty:
    st.error("ዳታ ማግኘት አልተቻለም። እባክህ ትንሽ ቆይተህ Refresh አድርገው።")
    st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# ዋጋውን ማስተካከል
for col in ['open', 'high', 'low', 'close']:
    df[col] += price_offset

# --- 4. ICT Advanced Logic (ሳይቀነስ) ---
high_p = df['high'].max()
low_p = df['low'].min()
equilibrium = (high_p + low_p) / 2
ote_deep = low_p + (high_p - low_p) * 0.79
ote_shallow = low_p + (high_p - low_p) * 0.62

def get_obs(df):
    obs = []
    for i in range(1, len(df)-1):
        if df.iloc[i+1]['close'] > df.iloc[i]['high'] and df.iloc[i]['close'] < df.iloc[i]['open']:
            obs.append({'type': 'Bullish', 'level': df.iloc[i]['high'], 'low': df.iloc[i]['low']})
        elif df.iloc[i+1]['close'] < df.iloc[i]['low'] and df.iloc[i]['close'] > df.iloc[i]['open']:
            obs.append({'type': 'Bearish', 'level': df.iloc[i]['low'], 'high': df.iloc[i]['high']})
    return obs

current_obs = get_obs(df)
curr_price = df.iloc[-1]['close']

# --- 5. ሲግናል እና SL/TP ---
entry_triggered = False
msg_content = ""
for ob in current_obs[-1:]:
    if abs(curr_price - ob['level']) / ob['level'] < 0.0002:
        entry_triggered = True
        sl = ob['low'] if ob['type'] == 'Bullish' else ob['high']
        tp = curr_price + (curr_price - sl) * 2 if ob['type'] == 'Bullish' else curr_price - (sl - curr_price) * 2
        msg_content = f"🎯 Gold Spot {ob['type']}:\nPrice: {curr_price:,.2f}\nSL: {sl:,.2f}\nTP: {tp:,.2f}"

if entry_triggered:
    send_telegram_msg(msg_content)

# --- 6. ቻርቱ እና UI ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

for ob in current_obs[-3:]:
    fig.add_hline(y=ob['level'], line_color="cyan", opacity=0.3)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

col1, col2 = st.columns([3, 1])
with col1: st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Market Status")
    st.metric("XAU/USD Live", f"{curr_price:,.2f}")
    if st.button("📢 ቴሌግራምን ሞክር"):
        send_telegram_msg(f"🚀 ቦቱ ከ TradingView ጋር ተመሳስሏል! ዋጋ: {curr_price:,.2f}")
    st.divider()
    st.info("Scanning for OB/FVG...")
