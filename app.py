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
st.set_page_config(page_title="XAU/USD Exact Sync", layout="wide")
st_autorefresh(interval=30000, key="live_update") # በየ 30 ሰከንዱ ራሱን ያድሳል

st.title("🏹 ICT Gold Spot (XAU/USD) - Exact Sync")

# --- 3. ዳታ ማውረድ (ቀጥታ Spot ዳታ) ---
# 'GC=F'ን ትተን በቀጥታ 'XAUUSD=X'ን እንጠቀማለን
@st.cache_data(ttl=30)
def load_exact_data():
    # Yahoo Finance ላይ Gold Spot የሚገኘው በዚህ ቲከር ነው
    d = yf.download("XAUUSD=X", period="2d", interval="5m")
    return d

data = load_exact_data()

if data.empty:
    st.warning("የ Spot ዳታ ለጊዜው አልተገኘም። እባክህ ገጹን Refresh አድርገው ወይም 1 ደቂቃ ጠብቅ።")
    st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# --- 4. ICT Advanced Logic ---
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

# --- 5. ሲግናል እና ትክክለኛ SL/TP ---
entry_triggered = False
msg_content = ""
for ob in current_obs[-1:]:
    if abs(curr_price - ob['level']) / ob['level'] < 0.0002:
        entry_triggered = True
        sl = ob['low'] if ob['type'] == 'Bullish' else ob['high']
        tp = curr_price + (curr_price - sl) * 2 if ob['type'] == 'Bullish' else curr_price - (sl - curr_price) * 2
        msg_content = f"🎯 Gold Spot {ob['type']} Entry:\nPrice: {curr_price:,.2f}\nSL: {sl:,.2f}\nTP: {tp:,.2f}"

if entry_triggered:
    send_telegram_msg(msg_content)

# --- 6. ቻርቱ እና UI ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

for ob in current_obs[-3:]:
    color = "cyan" if ob['type'] == 'Bullish' else "magenta"
    fig.add_hline(y=ob['level'], line_color=color, opacity=0.4)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

col1, col2 = st.columns([3, 1])
with col1: st.plotly_chart(fig, use_container_width=True)
with col2:
    st.subheader("Market Status")
    st.metric("XAU/USD (Spot)", f"{curr_price:,.2f}")
    if st.button("📢 ቴሌግራምን ሞክር"):
        send_telegram_msg(f"✅ ቦቱ አሁን ከ TradingView ጋር 100% ተመሳስሏል! ዋጋ: {curr_price:,.2f}")
    st.divider()
    if entry_triggered: st.success("🔥 Entry Found!")
    else: st.info("Scanning for ICT setups...")
