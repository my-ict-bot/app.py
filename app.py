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
st.set_page_config(page_title="ICT Gold Spot Terminal", layout="wide")
st_autorefresh(interval=60000, key="live_update")

st.title("🏹 ICT Gold Spot (XAU/USD) Terminal")

# Sidebar - Gold Spot (XAUUSD=X) በቋሚነት ተመርጧል
ticker = st.sidebar.selectbox("Asset", ["XAUUSD=X", "EURUSD=X", "GBPUSD=X", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["5m", "15m", "1h", "1d"])

# --- 3. ዳታ ማውረድ ---
data = yf.download(ticker, period="3d", interval=timeframe)
if data.empty: st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# --- 4. ICT Advanced Logic (ሳይቀነስ) ---
high_3d = df['high'].max()
low_3d = df['low'].min()
equilibrium = (high_3d + low_3d) / 2
ote_deep = low_3d + (high_3d - low_3d) * 0.79
ote_shallow = low_3d + (high_3d - low_3d) * 0.62

# FVG እና OB Detection (ልክ እንደበፊቱ)
def get_fvgs(df):
    fvgs = []
    for i in range(2, len(df)):
        if df.iloc[i-2]['high'] < df.iloc[i]['low']:
            fvgs.append({'type': 'Bullish', 'top': df.iloc[i]['low'], 'bottom': df.iloc[i-2]['high']})
        elif df.iloc[i-2]['low'] > df.iloc[i]['high']:
            fvgs.append({'type': 'Bearish', 'top': df.iloc[i-2]['low'], 'bottom': df.iloc[i]['high']})
    return fvgs

def get_obs(df):
    obs = []
    for i in range(1, len(df)-1):
        if df.iloc[i+1]['close'] > df.iloc[i]['high'] and df.iloc[i]['close'] < df.iloc[i]['open']:
            obs.append({'type': 'Bullish', 'level': df.iloc[i]['high'], 'low': df.iloc[i]['low']})
        elif df.iloc[i+1]['close'] < df.iloc[i]['low'] and df.iloc[i]['close'] > df.iloc[i]['open']:
            obs.append({'type': 'Bearish', 'level': df.iloc[i]['low'], 'high': df.iloc[i]['high']})
    return obs

current_fvgs = get_fvgs(df)
current_obs = get_obs(df)
curr_price = df.iloc[-1]['close']

# Market Phase ስሌት
last_change = ((df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5]) * 100
if abs(last_change) < 0.05: phase = "Consolidation 🛡️"
elif last_change > 0: phase = "Expansion (Bullish) 🚀"
else: phase = "Expansion (Bearish) 📉"

# --- 5. ሲግናል መላኪያ (OB ወይም FVG ሲነካ ብቻ) ---
entry_triggered = False
msg_content = ""

for ob in current_obs[-1:]:
    if abs(curr_price - ob['level']) / ob['level'] < 0.0003: # ለ Spot ይበልጥ ጥብቅ የተደረገ
        entry_triggered = True
        sl = ob['low'] if ob['type'] == 'Bullish' else ob['high']
        tp = curr_price + (curr_price - sl) * 2 if ob['type'] == 'Bullish' else curr_price - (sl - curr_price) * 2
        msg_content = f"🎯 Gold Spot {ob['type']} (OB):\nEntry: {curr_price:,.2f}\nSL: {sl:,.2f}\nTP: {tp:,.2f}"

if not entry_triggered:
    for fvg in current_fvgs[-1:]:
        if fvg['bottom'] <= curr_price <= fvg['top']:
            entry_triggered = True
            sl = fvg['bottom'] if fvg['type'] == 'Bullish' else fvg['top']
            tp = curr_price + (curr_price - sl) * 2 if fvg['type'] == 'Bullish' else curr_price - (sl - curr_price) * 2
            msg_content = f"🎯 Gold Spot {fvg['type']} (FVG):\nEntry: {curr_price:,.2f}\nSL: {sl:,.2f}\nTP: {tp:,.2f}"

if entry_triggered:
    send_telegram_msg(msg_content)

# --- 6. ቻርቱን መስራት ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="XAU/USD")])
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

for ob in current_obs[-3:]:
    color = "cyan" if ob['type'] == 'Bullish' else "magenta"
    fig.add_hline(y=ob['level'], line_color=color, line_width=1, opacity=0.4)

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

# --- 7. UI ማሳያ ---
c1, c2 = st.columns([3, 1])
with c1: st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Market Status")
    st.write(f"Phase: **{phase}**")
    if st.button("📢 ቴሌግራምን ሞክር"):
        send_telegram_msg("🚀 ቦቱ አሁን ከ Gold Spot (XAU/USD) ጋር ተገናኝቷል!")
    
    st.metric("XAU/USD Price", f"{curr_price:,.2f}")
    st.divider()
    if entry_triggered:
        st.success("🔥 ENTRY DETECTED!")
        st.write(msg_content)
    else:
        st.info("Scanning OB/FVG...")
    st.write(f"🕒 Sync: {datetime.now().strftime('%H:%M:%S')}")
