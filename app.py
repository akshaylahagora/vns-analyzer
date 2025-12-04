import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION (Must be first) ---
st.set_page_config(
    page_title="VNS Pro Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    
    /* VNS Status Badges */
    .status-bull { background-color: #d4edda; color: #155724; padding: 6px 12px; border-radius: 6px; font-weight: bold; border-left: 5px solid #28a745; display: inline-block; }
    .status-bear { background-color: #f8d7da; color: #721c24; padding: 6px 12px; border-radius: 6px; font-weight: bold; border-left: 5px solid #dc3545; display: inline-block; }
    .status-neutral { background-color: #e2e3e5; color: #383d41; padding: 6px 12px; border-radius: 6px; font-weight: bold; display: inline-block; }
    
    /* Make Radio Buttons look like Tabs/Pills */
    div[role="radiogroup"] > label > div:first-child {
        background-color: #fff;
        border: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. DYNAMIC STOCK LIST ---
STOCK_LIST = [
    "RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", 
    "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", 
    "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", 
    "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", 
    "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", 
    "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", 
    "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", 
    "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL",
    "VEDL", "SIEMENS", "IOC", "AMBUJACEM", "GAIL", "BANKBARODA", "CHOLAFIN", "TVSMOTOR"
]
STOCK_LIST.sort()

# --- 2. SESSION STATE INIT ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now() - timedelta(days=180) # Default 6M
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()

# Callback to update dates when Radio Button changes
def update_dates():
    selection = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    
    if selection == "1M":
        st.session_state.start_date = now - timedelta(days=30)
    elif selection == "3M":
        st.session_state.start_date = now - timedelta(days=90)
    elif selection == "6M":
        st.session_state.start_date = now - timedelta(days=180)
    elif selection == "1Y":
        st.session_state.start_date = now - timedelta(days=365)
    elif selection == "YTD":
        st.session_state.start_date = datetime(now.year, 1, 1)
    # If "Custom", we don't change dates automatically

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Stock Dropdown
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    
    st.divider()
    st.subheader("Time Period")
    
    # 1. RADIO BUTTONS (Horizontal)
    st.radio(
        "Quick Select:",
        options=["1M", "3M", "6M", "1Y", "YTD", "Custom"],
        index=2, # Default to 6M
        horizontal=True,
        key="duration_selector",
        on_change=update_dates
    )

    # 2. Date Pickers (Dynamic)
    date_range = st.date_input(
        "Date Range",
        value=(st.session_state.start_date, st.session_state.end_date),
        min_value=datetime(2000, 1, 1),
        max_value=datetime.now()
    )
    
    # Sync manual date picker changes back to session state
    if len(date_range) == 2:
        st.session_state.start_date = datetime.combine(date_range[0], datetime.min.time())
        st.session_state.end_date = datetime.combine(date_range[1], datetime.min.time())

    st.divider()
    run_btn = st.button("🚀 Run VNS Analysis", type="primary", use_container_width=True)


# --- MAIN LOGIC (VNS Engine) ---
@st.cache_data(ttl=300)
def fetch_nse_data(symbol, start, end):
    try:
        # Headers to mimic a real browser request to avoid NSE blocking
        headers = { 
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", 
            "Referer": "https://www.nseindia.com/" 
        }
        session = requests.Session()
        session.headers.update(headers)
        
        # Hit homepage to get cookies
        session.get("https://www.nseindia.com", timeout=5) 
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            df = pd.DataFrame(data)
            if df.empty: return None
            
            # Filter for Equity series only
            df = df[df['CH_SERIES'] == 'EQ'] 
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            
            # Convert columns to float
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
            
            return df.sort_values('Date').reset_index(drop=True)
        return None
    except: return None

def analyze_vns(df):
    results = []
    trend = "Neutral"
    last_bu, last_be = None, None
    
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        bu, be, signal, signal_type = None, None, "", ""
        
        if prev is not None:
            # 1. Determine Levels
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                bu = prev['CH_TRADE_HIGH_PRICE']
                last_bu = bu
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                be = prev['CH_TRADE_LOW_PRICE']
                last_be = be
            
            # 2. VNS Logic State Machine
            
            # Breakout/Breakdown
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu and trend != "Bullish":
                trend = "Bullish"
                signal = "TEJI (Breakout)"
                signal_type = "bull"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be and trend != "Bearish":
                trend = "Bearish"
                signal = "MANDI (Breakdown)"
                signal_type = "bear"
                
            # Atak (Reversal Warnings)
            elif trend == "Bullish" and last_bu and (row['CH_TRADE_HIGH_PRICE'] >= last_bu * 0.995) and row['CH_CLOSING_PRICE'] < last_bu:
                signal = "ATAK (Double Top)"
                signal_type = "warn"
            elif trend == "Bearish" and last_be and (row['CH_TRADE_LOW_PRICE'] <= last_be * 1.005) and row['CH_CLOSING_PRICE'] > last_be:
                signal = "ATAK (Double Bottom)"
                signal_type = "warn"
                
            # Reactions / Continuation
            else:
                if trend == "Bullish":
                    if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                        signal = "Reaction (Buy Dip)"; signal_type = "info"
                    elif row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                        signal = "Teji Continuation"; signal_type = "bull_light"
                elif trend == "Bearish":
                    if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                        signal = "Reaction (Sell Rise)"; signal_type = "info"
                    elif row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                        signal = "Mandi Continuation"; signal_type = "bear_light"

        results.append({
            'Date': row['Date'], 
            'Open': row['CH_OPENING_PRICE'], 
            'High': row['CH_TRADE_HIGH_PRICE'],
            'Low': row['CH_TRADE_LOW_PRICE'], 
            'Close': row['CH_CLOSING_PRICE'],
            'BU (Resist)': bu, 
            'BE (Support)': be, 
            'Signal': signal, 
            'Type': signal_type
        })
    return pd.DataFrame(results), trend, last_bu, last_be

# --- OUTPUT UI ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis from **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        
        if raw_df is not None:
            analyzed_df, trend, final_bu, final_be = analyze_vns(raw_df)
            
            # --- METRICS ROW ---
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("### Trend")
                if trend == "Bullish": st.markdown('<div class="status-bull">BULLISH (TEJI)</div>', unsafe_allow_html=True)
                elif trend == "Bearish": st.markdown('<div class="status-bear">BEARISH (MANDI)</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="status-neutral">NEUTRAL</div>', unsafe_allow_html=True)
            with c2: st.metric("Close", f"{analyzed_df.iloc[-1]['Close']:.2f}")
            with c3: st.metric("Resistance (BU)", f"{final_bu:.2f}" if final_bu else "-")
            with c4: st.metric("Support (BE)", f"{final_be:.2f}" if final_be else "-")

            st.divider()

            # --- STYLED TABLE LOGIC ---
            def style_vns(row):
                s = row['Type']
                
                # Styles
                bull = 'background-color: #d4edda; color: #155724; font-weight: bold'
                bear = 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                warn = 'background-color: #fff3cd; color: #856404; font-weight: bold'
                info = 'background-color: #e2e6ea; color: #0c5460; font-style: italic'
                
                if s == 'bull': return [bull] * len(row)
                if s == 'bear': return [bear] * len(row)
                if s == 'warn': return [warn] * len(row)
                if s == 'info': return [info] * len(row)
                return [''] * len(row)

            # Display Table (Hiding 'Type' via column_config instead of dropping it)
            st.dataframe(
                analyzed_df.style.apply(style_vns, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}",
                    "BU (Resist)": "{:.2f}", "BE (Support)": "{:.2f}"
                }, na_rep=""),
                column_config={
                    "Type": None  # <--- FIX: This hides the column but keeps it available for styling
                },
                use_container_width=True, 
                height=600
            )
        else:
            st.error("⚠️ Could not fetch data. NSE may be blocking the request. Please wait 10 seconds and try again.")
else:
    st.info("👈 Select options in the sidebar and click RUN.")
