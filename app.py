import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="VNS Pro Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR EXCEL LOOK ---
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    
    /* Global Font Tweak */
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* Metric Styling */
    div[data-testid="stMetricValue"] { 
        font-size: 1.6rem; font-weight: 700; color: #2c3e50;
    }
    
    /* Radio Button Tabs */
    div[role="radiogroup"] { flex-wrap: wrap; gap: 5px; }
    div[role="radiogroup"] label { 
        border: 1px solid #e0e0e0; 
        padding: 5px 15px; 
        border-radius: 5px; 
        background: #f8f9fa;
    }
    
    /* DataFrame specific tweaks to ensure height */
    div[data-testid="stDataFrame"] { width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
STOCK_LIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", 
    "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", 
    "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", 
    "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", 
    "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", 
    "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", 
    "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", 
    "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"
]
STOCK_LIST.sort()

# --- SESSION STATE ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now() - timedelta(days=60) # Default 2M
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()

def update_dates():
    selection = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    if selection == "1M": st.session_state.start_date = now - timedelta(days=30)
    elif selection == "2M": st.session_state.start_date = now - timedelta(days=60)
    elif selection == "3M": st.session_state.start_date = now - timedelta(days=90)
    elif selection == "6M": st.session_state.start_date = now - timedelta(days=180)
    elif selection == "1Y": st.session_state.start_date = now - timedelta(days=365)
    elif selection == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.subheader("Time Period")
    st.radio("Quick Select:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Date Range", value=(st.session_state.start_date, st.session_state.end_date), min_value=datetime(2000, 1, 1), max_value=datetime.now())
    if len(date_range) == 2:
        st.session_state.start_date = datetime.combine(date_range[0], datetime.min.time())
        st.session_state.end_date = datetime.combine(date_range[1], datetime.min.time())
    st.divider()
    run_btn = st.button("🚀 Run VNS Analysis", type="primary", use_container_width=True)

# --- FETCH DATA ---
@st.cache_data(ttl=300)
def fetch_nse_data(symbol, start, end):
    try:
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session(); session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            df = pd.DataFrame(response.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

# --- VNS LOGIC ---
def analyze_vns(df):
    df['BU'] = ""
    df['BE'] = ""
    trend = "Neutral"
    
    last_bu_level, last_be_level = None, None
    
    for i in range(1, len(df)):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        curr_high, curr_low = curr_row['CH_TRADE_HIGH_PRICE'], curr_row['CH_TRADE_LOW_PRICE']
        prev_high, prev_low = prev_row['CH_TRADE_HIGH_PRICE'], prev_row['CH_TRADE_LOW_PRICE']
        
        low_broken = curr_low < prev_low
        high_broken = curr_high > prev_high
        date_str = prev_row['Date'].strftime('%-d-%b').upper()
        
        # 1. ATAK CHECK
        if last_bu_level and (last_bu_level * 0.995 <= curr_high <= last_bu_level * 1.005) and curr_row['CH_CLOSING_PRICE'] < last_bu_level:
            df.at[i, 'BU'] = f"ATAK (Top)\n{curr_high}"
        if last_be_level and (last_be_level * 0.995 <= curr_low <= last_be_level * 1.005) and curr_row['CH_CLOSING_PRICE'] > last_be_level:
            df.at[i, 'BE'] = f"ATAK (Bottom)\n{curr_low}"

        # 2. TREND LOGIC
        if trend == "Bullish":
            if low_broken: 
                df.at[i-1, 'BU'] = f"BU(T) {date_str}\n{prev_high}"
                last_bu_level = prev_high 
            if high_broken: 
                df.at[i-1, 'BE'] = f"R(Teji)\n{prev_low}"
                last_be_level = prev_low 

        elif trend == "Bearish":
            if high_broken: 
                df.at[i-1, 'BE'] = f"BE(M) {date_str}\n{prev_low}"
                last_be_level = prev_low 
            if low_broken: 
                df.at[i-1, 'BU'] = f"R(Mandi) {date_str}\n{prev_high}"
                last_bu_level = prev_high 

        else: # Neutral
            if high_broken:
                trend = "Bullish"
                df.at[i-1, 'BE'] = f"Start Teji\n{prev_low}"
            elif low_broken:
                trend = "Bearish"
                df.at[i-1, 'BU'] = f"Start Mandi\n{prev_high}"
        
        # 3. SWITCHING
        if trend == "Bearish" and last_bu_level and curr_row['CH_CLOSING_PRICE'] > last_bu_level:
             trend = "Bullish"
             df.at[i, 'BU'] = "BREAKOUT (Teji)"
        if trend == "Bullish" and last_be_level and curr_row['CH_CLOSING_PRICE'] < last_be_level:
             trend = "Bearish"
             df.at[i, 'BE'] = "BREAKDOWN (Mandi)"
        
    return df

# --- OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df = analyze_vns(raw_df)
            
            # --- CREATE STACKED COLUMNS ---
            # Using HTML break <br/> won't work in pure Streamlit DataFrame unless we use a specific column config,
            # but standard \n works with white-space: pre-wrap style.
            
            analyzed_df['HIGH_LOW'] = analyzed_df['CH_TRADE_HIGH_PRICE'].astype(str) + "\n" + analyzed_df['CH_TRADE_LOW_PRICE'].astype(str)
            analyzed_df['OPEN_CLOSE'] = analyzed_df['CH_OPENING_PRICE'].astype(str) + "\n" + analyzed_df['CH_CLOSING_PRICE'].astype(str)
            
            display_df = analyzed_df[['Date', 'HIGH_LOW', 'OPEN_CLOSE', 'BU', 'BE']].copy()
            # Renaming columns to be cleaner
            display_df.columns = ['Date', 'High / Low', 'Open / Close', 'BU (Resist)', 'BE (Support)']
            
            # --- COLOR STYLING FUNCTION ---
            def style_excel(row):
                # Base Style: Centered, Middle Align, Border
                base = 'text-align: center; vertical-align: middle; white-space: pre-wrap; border-bottom: 1px solid #f0f0f0;'
                
                styles = [base] * len(row)
                
                # Colors
                c_bull = base + 'background-color: #d1e7dd; color: #0f5132; font-weight: bold;' 
                c_bear = base + 'background-color: #f8d7da; color: #842029; font-weight: bold;' 
                c_atak = base + 'background-color: #fff3cd; color: #664d03; font-weight: bold;' 
                c_info = base + 'background-color: #e2e3e5; color: #41464b; font-style: italic;' 
                
                # BU Column (Index 3)
                bu_txt = str(row['BU (Resist)'])
                if "BU(T)" in bu_txt or "BREAKOUT" in bu_txt: styles[3] = c_bull
                elif "R(" in bu_txt: styles[3] = c_info
                elif "ATAK" in bu_txt: styles[3] = c_atak
                elif "Mandi" in bu_txt: styles[3] = c_bear
                
                # BE Column (Index 4)
                be_txt = str(row['BE (Support)'])
                if "BE(M)" in be_txt or "BREAKDOWN" in be_txt: styles[4] = c_bear
                elif "R(" in be_txt: styles[4] = c_info
                elif "ATAK" in be_txt: styles[4] = c_atak
                elif "Teji" in be_txt: styles[4] = c_bull
                
                return styles

            # Render Table
            st.dataframe(
                display_df.style.apply(style_excel, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y")
                }),
                use_container_width=True,
                height=800,
                # Column Config for better widths
                column_config={
                    "Date": st.column_config.DateColumn("Date", format="DD-MMM-YYYY", width="small"),
                    "High / Low": st.column_config.TextColumn("High\nLow", width="small"),
                    "Open / Close": st.column_config.TextColumn("Open\nClose", width="small"),
                    "BU (Resist)": st.column_config.TextColumn("BU (Higher)", width="medium"),
                    "BE (Support)": st.column_config.TextColumn("BE (Lower)", width="medium")
                }
            )
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
