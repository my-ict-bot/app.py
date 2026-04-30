import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# የዌብሳይቱ ገጽታ ቅንጅት
st.set_page_config(page_title="ICT Market Maker Bot", layout="wide")

st.title("🏹 ICT Institutional Algorithm Bot")
st.subheader("Central Bank Price Action Analysis (Forex & Commodities)")

# Side Bar ለምርጫዎች
symbol = st.sidebar.selectbox("የሚተነተን Asset ምረጥ", ["EURUSD=X", "GBPUSD=X", "GC=F", "CL=F", "BTC-USD"])
timeframe = st.sidebar.selectbox("Timeframe", ["15m", "1h", "4h", "1d"])

def get_ict_data(symbol, tf):
    # ዳታውን ከ Yahoo Finance ማውረድ
    df = yf.download(symbol, period="5d", interval=tf)
 
    # የ ICT Liquidity ደረጃዎችን ማስላት
    df['PDH'] = df['High'].shift(1).rolling(window=20).max() # Previous Daily High lookback
    df['PDL'] = df['Low'].shift(1).rolling(window=20).min()  # Previous Daily Low lookback
 
    # Fair Value Gap (FVG) መለየት
    df['FVG_Up'] = (df['Low'] > df['High'].shift(2)) & (df['Close'].shift(1) > df['High'].shift(2))
    df['FVG_Down'] = (df['High'] < df['Low'].shift(2)) & (df['Close'].shift(1) < df['Low'].shift(2))
 
    return df

data = get_ict_data(symbol, timeframe)
if not data.empty:
    last_row = data.iloc[-1]
    # የተቀረው የኮድህ ክፍል እዚህ ይግባ
else:
    st.warning("ለተመረጠው Asset ዳታ ማግኘት አልተቻለም። እባክህ ሌላ ሞክር።")
prev_row = data.iloc[-2]

# --- ALGORITHM LOGIC (THE BRAIN) ---
st.write(f"### የተመረጠው: {symbol} ወቅታዊ ትንታኔ")

col1, col2, col3 = st.columns(3)

# ICT Logic: Liquidity Sweep + FVG Reversal
status = "Neutral ⚖️"
entry = 0
sl = 0
tp = 0
signal_color = "white"

# Bullish Setup: ዋጋ ከPDL በታች ወርዶ ከተመለሰ (Liquidity Raid)
# መረጃዎቹን ወደ ነጠላ ቁጥር (float) በመቀየር ማወዳደር
# መረጃው ዝርዝር ቢሆን እንኳ የመጀመሪያውን ነጠላ ቁጥር ብቻ እንዲወስድ ማድረግ
close_price = float(last_row['Close'].iloc[0] if hasattr(last_row['Close'], 'iloc') else last_row['Close'])
pdl_level = float(last_row['PDL'].iloc[0] if hasattr(last_row['PDL'], 'iloc') else last_row['PDL'])
prev_low = float(prev_row['Low'].iloc[0] if hasattr(prev_row['Low'], 'iloc') else prev_row['Low'])
pdl_level = float(last_row['PDL'])
prev_low = float(prev_row['Low'])

if close_price > pdl_level and prev_low < pdl_level:
    status = "Buy Signal"
    signal_color = "green"
    status = "BUY SIGNAL (Bullish Reversal)"
    entry = round(last_row['Close'], 5)
    sl = round(last_row['PDL'] - (last_row['PDL'] * 0.001), 5)
    tp = round(entry + (entry - sl) * 2, 5) # 1:2 Risk-Reward
    signal_color = "green"

# Bearish Setup: ዋጋ ከPDH በላይ ወጥቶ ከተመለሰ (Manipulation)
elif last_row['Close'] < last_row['PDH'] and prev_row['High'] > last_row['PDH']:
    status = "SELL SIGNAL (Bearish Reversal)"
    entry = round(last_row['Close'], 5)
    sl = round(last_row['PDH'] + (last_row['PDH'] * 0.001), 5)
    tp = round(entry - (sl - entry) * 2, 5)
    signal_color = "red"

# መረጃውን በዌብሳይቱ ላይ ማሳየት
with col1:
    st.metric("አሁኑ ዋጋ", f"{last_row['Close']:.5f}")
with col2:
    st.markdown(f"**ሁኔታ:** <span style='color:{signal_color}'>{status}</span>", unsafe_allow_html=True)

if entry != 0:
    st.success(f"✅ ተገኝቷል! Entry: {entry} | SL: {sl} | TP: {tp}")
else:
    st.info("ገበያው ትክክለኛውን የ Manipulation ዞን እየጠበቀ ነው...")

# ዳታውን በሰንጠረዥ ማሳየት
st.write("#### የቅርብ ጊዜ የዋጋ እንቅስቃሴዎች")
st.dataframe(data.tail(10))

st.markdown("---")
st.write("💡 **ማሳሰቢያ:** ይህ አልጎሪዝም 'Central Bank' ገበያውን manipulate የሚያደርጉባቸውን ዞኖች (Liquidity Voids) ለመለየት ታስቦ የተሰራ ነው።")
