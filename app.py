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

# --- MOBILE FRIENDLY CSS ---
st.markdown("""
<style>
    .stApp { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 1.5rem; font-weight: bold; }
    
    .status-bull { background-color: #d4edda; color: #155724; padding: 6px 12px; border-radius: 6px; font-weight: bold; border-left: 5px solid #28a745; display: inline-block; }
    .status-bear { background-color: #f8d7da; color: #721c24; padding: 6px 12px; border-radius: 6px; font-weight: bold; border-left: 5px solid #dc3545; display: inline-block; }
    .status-neutral { background-color: #e2e3e5; color: #383d41; padding: 6px 12px; border-radius: 6px; font-weight: bold; display: inline-block; }
    
    /* Tabs */
    div[role="radiogroup"] > label > div:first-child { background-color: #fff; border: 1px solid #ddd; }
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
    st.session_state.start_date = datetime.now() - timedelta(days=30)
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
    st.radio("Quick Select:", ["1M", "3M", "6M", "1Y", "YTD", "Custom"], index=0, horizontal=True, key="duration_selector", on_change=update_dates)
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

# --- VNS LOGIC ENGINE (UPDATED FROM EXCEL) ---
def analyze_vns(df):
    results = []
    trend = "Neutral"
    
    # Track the last established levels to determine signals
    last_bu = None
    last_be = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        prev = df.iloc[i-1] if i > 0 else None
        
        bu = None
        be = None
        signal = ""
        signal_type = ""
        
        if prev is not None:
            curr_high = row['CH_TRADE_HIGH_PRICE']
            curr_low = row['CH_TRADE_LOW_PRICE']
            prev_high = prev['CH_TRADE_HIGH_PRICE']
            prev_low = prev['CH_TRADE_LOW_PRICE']
            
            # --- BREAK TRIGGERS ---
            low_broken = curr_low < prev_low
            high_broken = curr_high > prev_high
            
            # --- SIGNAL LOGIC ---
            
            # 1. BULLISH SCENARIO (Teji)
            if trend == "Bullish":
                # High Broken -> Reaction Support (BE)
                if high_broken:
                    # Logic: Normally Prev Low, but if Outside Bar (Curr Low < Prev Low), mark Curr Low
                    val = min(prev_low, curr_low)
                    be = val
                    last_be = val
                    signal = "Reaction of Teji"
                    signal_type = "info"
                
                # Low Broken -> Trend Top (BU)
                if low_broken:
                    val = prev_high
                    bu = val
                    last_bu = val
                    signal = "BU (T)"
                    signal_type = "bull"
                    
                    # Check for Reversal (Double Top / Breakout Fail)
                    if last_bu and curr_high < last_bu and row['CH_CLOSING_PRICE'] < prev_low:
                         # Potential trend shift logic could go here
                         pass

            # 2. BEARISH SCENARIO (Mandi)
            elif trend == "Bearish":
                # High Broken -> Trend Bottom (BE)
                if high_broken:
                    val = prev_low
                    be = val
                    last_be = val
                    signal = "BE (M)"
                    signal_type = "bear"
                
                # Low Broken -> Reaction Resistance (BU)
                if low_broken:
                    # Logic: Normally Prev High, but if Outside Bar (Curr High > Prev High), mark Curr High
                    val = max(prev_high, curr_high)
                    bu = val
                    last_bu = val
                    signal = "Reaction of Mandi"
                    signal_type = "info" # Reactions are blue/info

            # 3. NEUTRAL / STARTUP
            else:
                if high_broken:
                    trend = "Bullish"
                    signal = "Trend Start (Teji)"
                    signal_type = "bull"
                elif low_broken:
                    trend = "Bearish"
                    signal = "Trend Start (Mandi)"
                    signal_type = "bear"
            
            # --- TREND SWITCH CHECKS ---
            # If we are in Mandi, but we break the last Reaction High (BU) -> Switch to Teji
            if trend == "Bearish" and last_bu and row['CH_CLOSING_PRICE'] > last_bu:
                trend = "Bullish"
                signal = "TEJI (Breakout)"
                signal_type = "bull"
            
            # If we are in Teji, but we break the last Reaction Low (BE) -> Switch to Mandi
            if trend == "Bullish" and last_be and row['CH_CLOSING_PRICE'] < last_be:
                trend = "Bearish"
                signal = "MANDI (Breakdown)"
                signal_type = "bear"

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

# --- OUTPUT ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner(f"Fetching data for {selected_stock}..."):
        raw_df = fetch_nse_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            analyzed_df, trend, final_bu, final_be = analyze_vns(raw_df)
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.caption("Current Trend")
                if trend == "Bullish": st.markdown('<div class="status-bull">BULLISH (TEJI)</div>', unsafe_allow_html=True)
                elif trend == "Bearish": st.markdown('<div class="status-bear">BEARISH (MANDI)</div>', unsafe_allow_html=True)
                else: st.markdown('<div class="status-neutral">NEUTRAL</div>', unsafe_allow_html=True)
            with c2: st.metric("Close", f"{analyzed_df.iloc[-1]['Close']:.2f}")
            with c3: st.metric("Res (BU)", f"{final_bu:.2f}" if final_bu else "-")
            with c4: st.metric("Sup (BE)", f"{final_be:.2f}" if final_be else "-")
            
            st.divider()

            def style_vns(row):
                s = row['Type']
                bull = 'background-color: #d4edda; color: #155724; font-weight: bold'
                bear = 'background-color: #f8d7da; color: #721c24; font-weight: bold'
                warn = 'background-color: #fff3cd; color: #856404; font-weight: bold'
                info = 'background-color: #e2e6ea; color: #0c5460; font-style: italic'
                if s == 'bull': return [bull] * len(row)
                if s == 'bear': return [bear] * len(row)
                if s == 'warn': return [warn] * len(row)
                if s == 'info': return [info] * len(row)
                return [''] * len(row)

            st.dataframe(
                analyzed_df.style.apply(style_vns, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", 
                    "Low": "{:.2f}", "Close": "{:.2f}", "BU (Resist)": "{:.2f}", "BE (Support)": "{:.2f}"
                }, na_rep=""),
                column_config={"Type": None}, use_container_width=True, height=600
            )
        else: st.error("⚠️ Could not fetch data.")
else: st.info("👈 Select options and click RUN.")
