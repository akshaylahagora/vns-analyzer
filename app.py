import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS (Clean Up) ---
st.markdown("""
<style>
    .stApp { background-color: white; }
    /* Make the table text larger and readable */
    .stDataFrame { font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
STOCK_LIST = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"]
STOCK_LIST.sort()

# --- STATE ---
if 'start_date' not in st.session_state: st.session_state.start_date = datetime.now() - timedelta(days=60)
if 'end_date' not in st.session_state: st.session_state.end_date = datetime.now()

def update_dates():
    sel = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)
    elif sel in days: st.session_state.start_date = now - timedelta(days=days[sel])

with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.radio("Period:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Range", (st.session_state.start_date, st.session_state.end_date))
    if len(date_range) == 2: st.session_state.start_date, st.session_state.end_date = [datetime.combine(d, datetime.min.time()) for d in date_range]
    st.divider()
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# --- DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers); s.get("https://www.nseindia.com", timeout=5)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=10)
        if r.status_code == 200:
            df = pd.DataFrame(r.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']: df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

# --- LOGIC ---
def analyze_vns(df):
    df['BU'], df['BE'] = "", ""
    df['Type'] = "" # Helper for styling
    trend = "Neutral"
    
    last_bu = None
    last_be = None
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = curr['CH_TRADE_HIGH_PRICE'], curr['CH_TRADE_LOW_PRICE'], curr['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        d_str = prev['Date'].strftime('%d-%b').upper()
        
        # ATAK
        if last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu:
            df.at[i, 'BU'] = f"ATAK (Top) {c_h}"
            df.at[i, 'Type'] = "warn"
        if last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be:
            df.at[i, 'BE'] = f"ATAK (Bottom) {c_l}"
            df.at[i, 'Type'] = "warn"

        # TREND
        if trend == "Bullish":
            if c_l < p_l: # Low Broken
                df.at[i-1, 'BU'] = f"BU(T) {d_str} : {p_h}"
                df.at[i-1, 'Type'] = "bull"
                last_bu = p_h
            if c_h > p_h: # High Broken
                df.at[i-1, 'BE'] = f"R(Teji) : {p_l}"
                df.at[i-1, 'Type'] = "info"
                last_be = p_l
        
        elif trend == "Bearish":
            if c_h > p_h: # High Broken
                df.at[i-1, 'BE'] = f"BE(M) {d_str} : {p_l}"
                df.at[i-1, 'Type'] = "bear"
                last_be = p_l
            if c_l < p_l: # Low Broken
                df.at[i-1, 'BU'] = f"R(Mandi) {d_str} : {p_h}"
                df.at[i-1, 'Type'] = "info"
                last_bu = p_h
                
        else: # Neutral
            if c_h > p_h: 
                trend = "Bullish"; df.at[i-1, 'BE'] = f"Start Teji : {p_l}"; df.at[i-1, 'Type']="bull"; last_be = p_l
            elif c_l < p_l: 
                trend = "Bearish"; df.at[i-1, 'BU'] = f"Start Mandi : {p_h}"; df.at[i-1, 'Type']="bear"; last_bu = p_h
            
        # SWITCH
        if trend == "Bearish" and last_bu and c_c > last_bu:
            trend = "Bullish"; df.at[i, 'BU'] = "BREAKOUT (Teji)"; df.at[i, 'Type']="bull"
        if trend == "Bullish" and last_be and c_c < last_be:
            trend = "Bearish"; df.at[i, 'BE'] = "BREAKDOWN (Mandi)"; df.at[i, 'Type']="bear"
            
    return df

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df = analyze_vns(raw_df)
            
            # --- PREPARE CLEAN TABLE ---
            disp_df = df[['Date', 'CH_OPENING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_CLOSING_PRICE', 'BU', 'BE', 'Type']].copy()
            disp_df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Resist)', 'BE (Support)', 'Type']
            
            # --- COLOR STYLING (The Safe Way) ---
            def color_rows(row):
                s = row['Type']
                # High Contrast Excel Colors
                if s == 'bull': return ['background-color: #C6EFCE; color: #006100; font-weight: bold'] * len(row)
                if s == 'bear': return ['background-color: #FFC7CE; color: #9C0006; font-weight: bold'] * len(row)
                if s == 'warn': return ['background-color: #FFEB9C; color: #9C5700; font-weight: bold'] * len(row)
                if s == 'info': return ['background-color: #E6F3FF; color: #000; font-style: italic'] * len(row)
                return [''] * len(row)

            # RENDER
            st.dataframe(
                disp_df.style.apply(color_rows, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                column_config={
                    "Type": None, # Hide the helper column
                    "BU (Resist)": st.column_config.TextColumn(width="medium"),
                    "BE (Support)": st.column_config.TextColumn(width="medium")
                },
                use_container_width=True,
                height=800
            )
        else: st.error("⚠️ Data Error")
else: st.info("👈 Click RUN")
