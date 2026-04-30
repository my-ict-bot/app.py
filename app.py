import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# የዌብሳይቱ ገጽታ
st.set_page_config(page_title="Pro Smart Money AI", layout="wide")
st.title("Central Bank Price Action Analysis (AI Predictor)")

# 1. Asset መምረጫ (Gold, Forex, Crypto ተጨምሯል)
assets = ["GC=F", "EURUSD=X", "GBPUSD=X", "BTC-USD", "ETH-USD", "SI=F", "CL=F", "^GSPC"]
ticker = st.sidebar.selectbox("የሚከታተሉት Asset ይምረጡ", assets)
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "30m", "1h", "4h", "1d"])

# 2. ዳታ ማውረድ
data = yf.download(ticker, period="5d", interval=timeframe)

if data.empty:
    st.error("ዳታ ማግኘት አልተቻለም። እባክህ ገበያው ክፍት መሆኑን አረጋግጥ።")
    st.stop()

# 3. Smart Money Indicators (PDH, PDL, FVG, OB)
data['PDH'] = data['High'].shift(1).rolling(window=24).max()
data['PDL'] = data['Low'].shift(1).rolling(window=24).min()

# FVG (Fair Value Gap)
data['FVG_Up'] = (data['Low'] > data['High'].shift(2))
data['FVG_Down'] = (data['High'] < data['Low'].shift(2))

# 4. መረጃዎችን ወደ ነጠላ ቁጥር መቀየር (ስህተትን ለመከላከል)
def safe_float(val):
    try:
        return float(val.iloc[-1]) if hasattr(val, 'iloc') else float(val)
    except: return 0.0

last_row = data.iloc[-1]
prev_row = data.iloc[-2]

c_price = safe_float(last_row['Close'])
pdl_val = safe_float(last_row['PDL'])
pdh_val = safe_float(last_row['PDH'])
p_low = safe_float(prev_row['Low'])
p_high = safe_float(prev_row['High'])
# መስመር 44 እና 45 ላይ ያሉትን በዚህ ተካቸው
fvg_up = bool(last_row['FVG_Up'].any()) if hasattr(last_row['FVG_Up'], 'any') else bool(last_row['FVG_Up'])
fvg_down = bool(last_row['FVG_Down'].any()) if hasattr(last_row['FVG_Down'], 'any') else bool(last_row['FVG_Down'])

# 5. AI Signal & Prediction Logic
status = "🔎 ገበያው ትክክለኛውን ዞን እየጠበቀ ነው..."
signal_color = "white"
entry, sl, tp = 0, 0, 0

# BUY Logic: Liquidity Sweep + FVG Confirmation
if c_price > pdl_val and p_low < pdl_val and fvg_up:
    status = "🔥 PRO BUY SIGNAL (Manipulation Detected)"
    signal_color = "green"
    entry = round(c_price, 5)
    sl = round(pdl_val - (pdl_val * 0.001), 5)
    tp = round(entry + (entry - sl) * 3, 5)

# SELL Logic: Liquidity Sweep + FVG Confirmation
elif c_price < pdh_val and p_high > pdh_val and fvg_down:
    status = "⚠️ PRO SELL SIGNAL (Manipulation Detected)"
    signal_color = "red"
    entry = round(c_price, 5)
    sl = round(pdh_val + (pdh_val * 0.001), 5)
    tp = round(entry - (sl - entry) * 3, 5)

# 6. ውጤቱን ማሳየት
col1, col2 = st.columns(2)
with col1:
    st.metric(f"ወቅታዊ የ {ticker} ዋጋ", f"{c_price:.5f}")
with col2:
    st.markdown(f"### **ሁኔታ:** <span style='color:{signal_color}'>{status}</span>", unsafe_allow_html=True)

if entry != 0:
    st.balloons()
    st.success(f"🎯 **TARGET FOUND!** \n\n **Entry:** {entry} | **SL:** {sl} | **TP:** {tp}")
    # የድምፅ ማስጠንቀቂያ
    st.components.v1.html('<audio autoplay><source src="https://www.soundjay.com/buttons/beep-01a.mp3"></audio>', height=0)

# 7. የዋጋ ሰንጠረዥ
st.write("#### የቅርብ ጊዜ የዋጋ እንቅስቃሴዎች")
st.dataframe(data.tail(10))

st.markdown("---")
st.info("💡 **ጠቃሚ መረጃ:** ይህ AI 'Smart Money Concepts' (SMC) በመጠቀም ገበያው ወዴት ሊሄድ እንደሚችል ይተነብያል።")
