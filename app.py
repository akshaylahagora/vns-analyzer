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
    
    /* Excel-like Table Styling */
    .dataframe { font-family: Arial, sans-serif; font-size: 14px; }
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
    st.radio("Quick Select:", ["1M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
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
    # Initialize columns as Object (String) to hold text
    df['BU'] = ""
    df['BE'] = ""
    
    trend = "Neutral"
    
    # We loop through index to allow "Look Back" editing
    for i in range(1, len(df)):
        curr_row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        curr_high = curr_row['CH_TRADE_HIGH_PRICE']
        curr_low = curr_row['CH_TRADE_LOW_PRICE']
        prev_high = prev_row['CH_TRADE_HIGH_PRICE']
        prev_low = prev_row['CH_TRADE_LOW_PRICE']
        
        # 1. Check Breaks
        low_broken = curr_low < prev_low
        high_broken = curr_high > prev_high
        
        # 2. Logic Machine
        
        # --- IF TREND IS BULLISH (Teji) ---
        if trend == "Bullish":
            # A. Low Broken -> This confirms the TOP.
            if low_broken:
                # Mark the Previous Day (Source of High) as BU
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                df.at[i-1, 'BU'] = f"BU(T) {date_str}\n{prev_high}"
                
                # Check for Reversal (Breakout Failure / Double Top logic can be added here)
                
            # B. High Broken -> This confirms the Dip was just a Reaction.
            if high_broken:
                # Mark the Previous Day (Source of Low) as Reaction Support
                # Note: If it's an outside bar scenario, we might need more complex logic, 
                # but standard VNS marks the previous low.
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                df.at[i-1, 'BE'] = f"R(Reaction of Teji)\n{prev_low}"

        # --- IF TREND IS BEARISH (Mandi) ---
        elif trend == "Bearish":
            # A. High Broken -> This confirms the BOTTOM.
            if high_broken:
                # Mark the Previous Day (Source of Low) as BE
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                df.at[i-1, 'BE'] = f"BE(M) {date_str}\n{prev_low}"
                
            # B. Low Broken -> This confirms the Rally was just a Reaction.
            if low_broken:
                # Mark the Previous Day (Source of High) as Reaction Resistance
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                df.at[i-1, 'BU'] = f"R(Reaction of Mandi) {date_str}\n{prev_high}"

        # --- IF NEUTRAL (Startup) ---
        else:
            if high_broken:
                trend = "Bullish"
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                # Mark start of Teji
                df.at[i-1, 'BE'] = f"Start Teji\n{prev_low}"
            elif low_broken:
                trend = "Bearish"
                date_str = prev_row['Date'].strftime('%-d-%b-%y').upper()
                # Mark start of Mandi
                df.at[i-1, 'BU'] = f"Start Mandi\n{prev_high}"
        
        # --- TREND SWITCHING ---
        # Check if we broke a MAJOR level established in the text
        # (This is complex to parse back from text, so we track logic state essentially)
        # For simple visual replication, the logic above covers the labeling.
        # To strictly switch trend variable:
        
        # If in Bearish, and we break a confirmed BU level -> Switch to Bullish
        # If in Bullish, and we break a confirmed BE level -> Switch to Bearish
        # (Simplified for this display version)
        if trend == "Bearish" and df.at[i-1, 'BU'] and "BU" in str(df.at[i-1, 'BU']) and curr_high > prev_high: 
             trend = "Bullish" # Potential switch
        
    return df

# --- OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df = analyze_vns(raw_df)
            
            # --- DISPLAY TABLE (EXCEL LAYOUT) ---
            # Format numbers and dates
            display_df = analyzed_df[['Date', 'CH_OPENING_PRICE', 'CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_CLOSING_PRICE', 'BU', 'BE']].copy()
            display_df.columns = ['Date', 'OPEN', 'HIGH', 'LOW', 'CLOSE', 'BU (High is Higher)', 'BE (Low is Lower)']
            
            # Helper to style rows
            def style_excel(row):
                return [''] * len(row)

            # Show Dataframe
            st.dataframe(
                display_df.style.format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "OPEN": "{:.2f}", "HIGH": "{:.2f}", "LOW": "{:.2f}", "CLOSE": "{:.2f}"
                }),
                use_container_width=True,
                height=800,
                column_config={
                    "BU (High is Higher)": st.column_config.TextColumn(width="medium"),
                    "BE (Low is Lower)": st.column_config.TextColumn(width="medium")
                }
            )
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
