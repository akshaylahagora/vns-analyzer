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

# --- CUSTOM CSS FOR "PRO" LOOK ---
st.markdown("""
<style>
    /* Main Background */
    .stApp { background-color: #f8f9fa; }
    
    /* Metrics Styling */
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    
    /* Custom Status Badges */
    .status-bull { background-color: #d4edda; color: #155724; padding: 5px 10px; border-radius: 5px; font-weight: bold; border-left: 5px solid #28a745; }
    .status-bear { background-color: #f8d7da; color: #721c24; padding: 5px 10px; border-radius: 5px; font-weight: bold; border-left: 5px solid #dc3545; }
    .status-neutral { background-color: #e2e3e5; color: #383d41; padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    
    /* Table Styling overrides are handled via Pandas Styler in the code */
</style>
""", unsafe_allow_html=True)

# --- 1. DYNAMIC STOCK LIST (NIFTY 500 SAMPLE) ---
# A comprehensive list to make the dropdown feel "dynamic"
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

# --- 2. SESSION STATE FOR DATES ---
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.now() - timedelta(days=180)
if 'end_date' not in st.session_state:
    st.session_state.end_date = datetime.now()

# Function to handle preset buttons
def set_date_range(days):
    st.session_state.end_date = datetime.now()
    if days == "YTD":
        st.session_state.start_date = datetime(datetime.now().year, 1, 1)
    else:
        st.session_state.start_date = datetime.now() - timedelta(days=days)

# --- SIDEBAR UI ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Dynamic Searchable Dropdown
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK"))
    
    st.subheader("Date Range")
    
    # Preset Buttons in a grid
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("1M"): set_date_range(30)
    if c2.button("3M"): set_date_range(90)
    if c3.button("6M"): set_date_range(180)
    if c4.button("1Y"): set_date_range(365)
    if st.button("YTD (Year to Date)", use_container_width=True): set_date_range("YTD")

    # Date Pickers (Connected to Session State)
    date_range = st.date_input(
        "Custom Range",
        value=(st.session_state.start_date, st.session_state.end_date),
        key="date_range_picker"
    )
    
    # Update session state if user manually changes picker
    if len(date_range) == 2:
        st.session_state.start_date = datetime.combine(date_range[0], datetime.min.time())
        st.session_state.end_date = datetime.combine(date_range[1], datetime.min.time())

    st.divider()
    run_btn = st.button("🚀 Run VNS Analysis", type="primary", use_container_width=True)

# --- MAIN APP LOGIC ---

@st.cache_data(ttl=300)
def fetch_nse_data(symbol, start, end):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.nseindia.com/",
            "Accept-Language": "en-US,en;q=0.9"
        }
        session = requests.Session()
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5) # Get cookies
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json().get('data', [])
            df = pd.DataFrame(data)
            if df.empty: return None
            
            df = df[df['CH_SERIES'] == 'EQ'] # Filter Equity
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for col in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']:
                df[col] = df[col].astype(float)
                
            return df.sort_values('Date').reset_index(drop=True)
        return None
    except Exception as e:
        return None

def analyze_vns(df):
    results = []
    trend = "Neutral"
    last_bu, last_be = None, None
    
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        bu, be, signal, signal_type = None, None, "", ""
        
        if prev is not None:
            # Set Levels
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                bu = prev['CH_TRADE_HIGH_PRICE']
                last_bu = bu
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                be = prev['CH_TRADE_LOW_PRICE']
                last_be = be
                
            # Logic
            # 1. Breakout/Breakdown
            if last_bu and row['CH_CLOSING_PRICE'] > last_bu and trend != "Bullish":
                trend = "Bullish"
                signal = "TEJI (Breakout)"
                signal_type = "bull"
            elif last_be and row['CH_CLOSING_PRICE'] < last_be and trend != "Bearish":
                trend = "Bearish"
                signal = "MANDI (Breakdown)"
                signal_type = "bear"
            
            # 2. Atak (Double Top/Bottom)
            elif trend == "Bullish" and last_bu and (row['CH_TRADE_HIGH_PRICE'] >= last_bu * 0.995) and row['CH_CLOSING_PRICE'] < last_bu:
                signal = "ATAK (Double Top)"
                signal_type = "warn"
            elif trend == "Bearish" and last_be and (row['CH_TRADE_LOW_PRICE'] <= last_be * 1.005) and row['CH_CLOSING_PRICE'] > last_be:
                signal = "ATAK (Double Bottom)"
                signal_type = "warn"
                
            # 3. Reactions
            else:
                if trend == "Bullish":
                    if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                        signal = "Reaction (Buy Dip)"
                        signal_type = "info"
                    elif row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                        signal = "Teji Continuation"
                        signal_type = "bull_light"
                elif trend == "Bearish":
                    if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']:
                        signal = "Reaction (Sell Rise)"
                        signal_type = "info"
                    elif row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']:
                        signal = "Mandi Continuation"
                        signal_type = "bear_light"

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

# --- HEADER SECTION ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis from **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching Data & Calculating VNS Levels..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        
        if raw_df is not None:
            analyzed_df, trend, final_bu, final_be = analyze_vns(raw_df)
            
            # --- DASHBOARD METRICS ---
            # Create a nice layout for key numbers
            m1, m2, m3, m4 = st.columns(4)
            
            # Trend Color Logic
            trend_color = "normal"
            if trend == "Bullish": trend_color = "off" # We use custom badge instead
            
            with m1:
                st.markdown("### Current Trend")
                if trend == "Bullish":
                    st.markdown('<div class="status-bull">BULLISH (TEJI)</div>', unsafe_allow_html=True)
                elif trend == "Bearish":
                    st.markdown('<div class="status-bear">BEARISH (MANDI)</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="status-neutral">NEUTRAL</div>', unsafe_allow_html=True)
            
            with m2:
                st.metric("Last Close", f"{analyzed_df.iloc[-1]['Close']:.2f}")
            
            with m3:
                st.metric("Key Resistance (BU)", f"{final_bu:.2f}" if final_bu else "-")
            
            with m4:
                st.metric("Key Support (BE)", f"{final_be:.2f}" if final_be else "-")

            st.divider()

            # --- STYLED DATAFRAME ---
            # This is where we apply the colors to the rows based on the signal
            def style_vns(row):
                s = row['Type']
                base_style = ''
                if s == 'bull': return ['background-color: #d4edda; color: #155724; font-weight: bold'] * len(row)
                if s == 'bear': return ['background-color: #f8d7da; color: #721c24; font-weight: bold'] * len(row)
                if s == 'warn': return ['background-color: #fff3cd; color: #856404; font-weight: bold'] * len(row)
                if s == 'info': return ['background-color: #e2e6ea; color: #0c5460; font-style: italic'] * len(row)
                return [''] * len(row)

            # Format numbers for clean display
            display_df = analyzed_df.drop(columns=['Type']) # Hide the helper column
            
            st.dataframe(
                display_df.style
                .apply(style_vns, axis=1)
                .format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}",
                    "BU (Resist)": "{:.2f}", "BE (Support)": "{:.2f}"
                }, na_rep=""),
                use_container_width=True,
                height=600
            )

        else:
            st.error("⚠️ Unable to fetch data. This usually happens because NSE blocks automated requests. Please wait 10 seconds and try again, or try a shorter date range.")

else:
    st.info("👈 Select a stock and click 'Run VNS Analysis' to start.")
