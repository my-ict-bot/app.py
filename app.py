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
st.set_page_config(page_title="Gold Master Sync", layout="wide")
st_autorefresh(interval=30000, key="live_update")

st.title("🏹 ICT Gold Spot (XAU/USD) - Precise Feed")

# --- 3. ዳታ አወራረድ (ከ TradingView ጋር የተቀራረበ) ---
@st.cache_data(ttl=30)
def load_gold_data():
    # GC=F (Futures) ዳታ በጣም ፈጣን እና አስተማማኝ ነው
    d = yf.download("GC=F", period="2d", interval="5m")
    # በምስልህ ላይ ባየሁት መሰረት ልዩነቱን ወደ -11.85 አድርጌዋለሁ
    return d, -11.85

data, offset = load_gold_data()

if data.empty:
    st.error("ዳታ አልተገኘም። እባክህ ገጹን Refresh አድርገው።")
    st.stop()

df = data.reset_index()
df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]

# ዋጋ ማስተካከያ
for col in ['open', 'high', 'low', 'close']:
    df[col] += offset

curr_price = df.iloc[-1]['close']

# --- 4. ICT Logic (OTE & OB) ---
high_p = df['high'].max()
low_p = df['low'].min()
equilibrium = (high_p + low_p) / 2
ote_deep = low_p + (high_p - low_p) * 0.79
ote_shallow = low_p + (high_p - low_p) * 0.62

def find_latest_ob(df):
    for i in range(len(df)-2, len(df)-15, -1):
        # Bullish OB
        if df.iloc[i+1]['close'] > df.iloc[i]['high'] and df.iloc[i]['close'] < df.iloc[i]['open']:
            return {'type': 'Bullish', 'level': df.iloc[i]['high'], 'sl': df.iloc[i]['low']}
        # Bearish OB
        if df.iloc[i+1]['close'] < df.iloc[i]['low'] and df.iloc[i]['close'] > df.iloc[i]['open']:
            return {'type': 'Bearish', 'level': df.iloc[i]['low'], 'sl': df.iloc[i]['high']}
    return None

ob = find_latest_ob(df)

# --- 5. ሲግናል መላኪያ ---
if ob:
    # ዋጋው ወደ OB ሲጠጋ (0.02% range)
    if abs(curr_price - ob['level']) / ob['level'] < 0.0002:
        tp_dist = abs(curr_price - ob['sl']) * 2
        tp = curr_price + tp_dist if ob['type'] == 'Bullish' else curr_price - tp_dist
        
        msg = (f"🎯 **Gold {ob['type']} Entry**\n"
               f"Price: {curr_price:,.2f}\n"
               f"SL: {ob['sl']:,.2f}\n"
               f"TP: {tp:,.2f}")
        
        if 'last_alert' not in st.session_state or st.session_state.last_alert != ob['level']:
            send_telegram_msg(msg)
            st.session_state.last_alert = ob['level']

# --- 6. ቻርቱ እና UI ---
fig = go.Figure(data=[go.Candlestick(x=df.iloc[:,0], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
fig.add_hline(y=equilibrium, line_dash="dot", line_color="yellow", annotation_text="Equilibrium")
fig.add_hrect(y0=ote_shallow, y1=ote_deep, fillcolor="gold", opacity=0.1, line_width=0, annotation_text="OTE Zone")

if ob:
    fig.add_hline(y=ob['level'], line_color="cyan", annotation_text=f"Last {ob['type']} OB")

fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)

c1, c2 = st.columns([3, 1])
with c1: st.plotly_chart(fig, use_container_width=True)
with c2:
    st.subheader("Market Sync")
    st.metric("XAU/USD Live", f"{curr_price:,.2f}")
    if st.button("📢 ቴሌግራም ሞክር"):
        send_telegram_msg(f"✅ ቦቱ በትክክል ተመሳስሏል! ዋጋ: {curr_price:,.2f}")
    st.divider()
    st.write(f"Updated: {datetime.now().strftime('%H:%M:%S')}")
