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

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: bold; }
    
    /* Make Radio Buttons look like Tabs */
    div[role="radiogroup"] { flex-wrap: wrap; }
    div[role="radiogroup"] > label > div:first-child {
        background-color: #fff; border: 1px solid #ddd;
    }
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
    # UPDATED: Default to 60 days (2 Months)
    st.session_state.start_date = datetime.now() - timedelta(days=60)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()

def update_dates():
    selection = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    if selection == "1M": st.session_state.start_date = now - timedelta(days=30)
    elif selection == "2M": st.session_state.start_date = now - timedelta(days=60) # Added 2M
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
    
    # UPDATED: Added "2M" and set index=1 (which is 2M) as default
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

# --- VNS LOGIC (EXCEL STYLE) ---
def analyze_vns(df):
    df['BU'] = ""
    df['BE'] = ""
    trend = "Neutral"
    
    for i in range(1, len(df)):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        curr_high = curr_row['CH_TRADE_HIGH_PRICE']
        curr_low = curr_row['CH_TRADE_LOW_PRICE']
        prev_high = prev_row['CH_TRADE_HIGH_PRICE']
        prev_low = prev_row['CH_TRADE_LOW_PRICE']
        
        low_broken = curr_low < prev_low
        high_broken = curr_high > prev_high
        
        # LOGIC MACHINE
        if trend == "Bullish":
            if low_broken: # Top Confirmed
                date_str = prev_row['Date'].strftime('%-d-%b').upper()
                df.at[i-1, 'BU'] = f"BU(T) {date_str}\n{prev_high}"
            if high_broken: # Reaction
                date_str = prev_row['Date'].strftime('%-d-%b').upper()
                df.at[i-1, 'BE'] = f"R(Teji)\n{prev_low}"

        elif trend == "Bearish":
            if high_broken: # Bottom Confirmed
                date_str = prev_row['Date'].strftime('%-d-%b').upper()
                df.at[i-1, 'BE'] = f"BE(M) {date_str}\n{prev_low}"
            if low_broken: # Reaction
                date_str = prev_row['Date'].strftime('%-d-%b').upper()
                df.at[i-1, 'BU'] = f"R(Mandi) {date_str}\n{prev_high}"

        else: # Neutral
            if high_broken:
                trend = "Bullish"
                df.at[i-1, 'BE'] = f"Start Teji\n{prev_low}"
            elif low_broken:
                trend = "Bearish"
                df.at[i-1, 'BU'] = f"Start Mandi\n{prev_high}"
        
        # Simple Switch Logic
        if trend == "Bearish" and df.at[i-1, 'BU'] and "BU" in str(df.at[i-1, 'BU']) and curr_high > prev_high: 
             trend = "Bullish"
        if trend == "Bullish" and df.at[i-1, 'BE'] and "BE" in str(df.at[i-1, 'BE']) and curr_low < prev_low:
             trend = "Bearish"
        
    return df

# --- OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df = analyze_vns(raw_df)
            
            # Prepare Display DF
            display_df = analyzed_df[['Date', 'CH_OPENING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_CLOSING_PRICE', 'BU', 'BE']].copy()
            display_df.columns = ['Date', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'BU (High)', 'BE (Low)']
            
            # --- COLOR STYLING FUNCTION ---
            def style_excel(row):
                styles = [''] * len(row)
                
                # Colors
                color_bull = 'background-color: #d1e7dd; color: #0f5132; font-weight: bold; white-space: pre-wrap;' # Green
                color_bear = 'background-color: #f8d7da; color: #842029; font-weight: bold; white-space: pre-wrap;' # Red
                color_info = 'background-color: #e2e3e5; color: #41464b; font-style: italic; white-space: pre-wrap;' # Grey/Blue
                
                # Check BU Column (Index 5)
                bu_text = str(row['BU (High)'])
                if "BU" in bu_text: styles[5] = color_bull
                elif "R(" in bu_text: styles[5] = color_info
                elif "Start" in bu_text: styles[5] = color_bear # Start Mandi
                
                # Check BE Column (Index 6)
                be_text = str(row['BE (Low)'])
                if "BE" in be_text: styles[6] = color_bear
                elif "R(" in be_text: styles[6] = color_info
                elif "Start" in be_text: styles[6] = color_bull # Start Teji
                
                return styles

            # Show Dataframe with Colors
            st.dataframe(
                display_df.style.apply(style_excel, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "OPEN": "{:.2f}", "HIGH": "{:.2f}", "LOW": "{:.2f}", "CLOSE": "{:.2f}"
                }),
                use_container_width=True,
                height=800,
                column_config={
                    "BU (High)": st.column_config.TextColumn(width="medium"),
                    "BE (Low)": st.column_config.TextColumn(width="medium")
                }
            )
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
