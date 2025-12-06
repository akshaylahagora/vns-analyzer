import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Logic Test", page_icon="🛠️", layout="wide")

st.title("🛠️ New VNS Logic Test")
st.markdown("Testing new rules: **Higher Highs (Teji)**, **Lower Lows (Mandi)**, and **Reaction Point Reversals (Atak)**.")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* TABLE STYLES */
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    
    /* COLORS */
    .c-bull { background-color: #C6EFCE; color: #006100; font-weight: bold; } /* Green */
    .c-bear { background-color: #FFC7CE; color: #9C0006; font-weight: bold; } /* Red */
    .c-atak { background-color: #FFEB9C; color: #9C5700; font-weight: bold; } /* Yellow */
    .c-info { background-color: #E6F3FF; color: #000000; font-style: italic;} /* Blue */
    
    .stSidebar label { color: #333 !important; }
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

# --- STATE ---
if 'test_start_date' not in st.session_state: st.session_state.test_start_date = datetime.now() - timedelta(days=60)

def update_dates():
    sel = st.session_state.duration_select
    now = datetime.now()
    if sel == "1M": st.session_state.test_start_date = now - timedelta(days=30)
    elif sel == "2M": st.session_state.test_start_date = now - timedelta(days=60)
    elif sel == "3M": st.session_state.test_start_date = now - timedelta(days=90)
    elif sel == "6M": st.session_state.test_start_date = now - timedelta(days=180)
    elif sel == "1Y": st.session_state.test_start_date = now - timedelta(days=365)

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    
    st.subheader("Time Period")
    st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y", "Custom"], index=1, horizontal=True, key="duration_select", on_change=update_dates)
    
    st.divider()
    st.subheader("Price Filter (Validation)")
    min_p = st.number_input("Min Price", 0, value=1000)
    max_p = st.number_input("Max Price", 0, value=100000)
    
    st.divider()
    run_btn = st.button("🚀 Verify New Logic", type="primary", use_container_width=True)

# --- DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start):
    try:
        yf_symbol = f"{symbol}.NS"
        # Fetch extra history for calculation context
        req_start = start - timedelta(days=30)
        df = yf.download(yf_symbol, start=req_start, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- 🛠️ NEW LOGIC ---
def analyze_new_logic(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    # State Variables
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    reaction_support = df.iloc[0]['Low']
    reaction_resist = df.iloc[0]['High']
    
    # Track Indices for "Between" calculation
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_high, c_low, c_open, c_close = curr['High'], curr['Low'], curr['Open'], curr['Close']
        date_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- TEJI (UPTREND) ---
        if trend == "Teji":
            # 1. Higher High? -> Continuation
            if c_high > last_peak:
                # MARK TEJI (T)
                df.at[i, 'BU'] = f"BU(T) {date_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                
                # REACTION: Find Low between Prev High and This High
                # Slice from last_peak_idx to current i
                swing_data = df.iloc[last_peak_idx:i+1]
                lowest_low = swing_data['Low'].min()
                
                reaction_support = lowest_low
                
                # Mark Reaction Support (Usually on the day the high breaks, we establish the support)
                df.at[i, 'BE'] = f"R(Reaction of Teji)\n{reaction_support:.2f}"
                df.at[i, 'Type'] = "bull" # Keep row green to show success
                
                # Update Pointers
                last_peak = c_high
                last_peak_idx = i
                
            # 2. Support Broken? -> Reversal (Atak/Mandi)
            elif c_low < reaction_support:
                # The peak we just made/held is now an ATAK (Double Top / Failed)
                df.at[i, 'BU'] = f"ATAK (Top)\n{last_peak:.2f}"
                
                # Switch Trend
                trend = "Mandi"
                df.at[i, 'BE'] = f"BE(M) {date_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                
                last_trough = c_low
                last_trough_idx = i
                reaction_resist = c_high # Initialize resistance for new downtrend

        # --- MANDI (DOWNTREND) ---
        elif trend == "Mandi":
            # 1. Lower Low? -> Continuation
            if c_low < last_trough:
                # MARK MANDI (M)
                df.at[i, 'BE'] = f"BE(M) {date_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                
                # REACTION: Find High between Prev Low and This Low
                swing_data = df.iloc[last_trough_idx:i+1]
                highest_high = swing_data['High'].max()
                
                reaction_resist = highest_high
                
                # Mark Reaction Resistance
                df.at[i, 'BU'] = f"R(Reaction of Mandi)\n{reaction_resist:.2f}"
                df.at[i, 'Type'] = "bear" # Keep row red
                
                # Update Pointers
                last_trough = c_low
                last_trough_idx = i
                
            # 2. Resistance Broken? -> Reversal (Atak/Teji)
            elif c_high > reaction_resist:
                # The trough is now ATAK (Bottom)
                df.at[i, 'BE'] = f"ATAK (Bottom)\n{last_trough:.2f}"
                
                # Switch Trend
                trend = "Teji"
                df.at[i, 'BU'] = f"BU(T) {date_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                
                last_peak = c_high
                last_peak_idx = i
                reaction_support = c_low # Init support for new uptrend

        # --- NEUTRAL / STARTUP ---
        else:
            if c_high > last_peak:
                trend = "Teji"
                df.at[i, 'BU'] = f"Start Teji\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                last_peak = c_high; last_peak_idx = i
                reaction_support = df.iloc[i-1]['Low']
            elif c_low < last_trough:
                trend = "Mandi"
                df.at[i, 'BE'] = f"Start Mandi\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                last_trough = c_low; last_trough_idx = i

    return df

# --- RENDER ---
if run_btn:
    with st.spinner(f"Fetching {selected_stock}..."):
        raw_df = fetch_data(selected_stock, st.session_state.test_start_date)
        
        if raw_df is not None:
            last_price = raw_df.iloc[-1]['Close']
            if not (min_p <= last_price <= max_p):
                st.warning(f"⚠️ Stock Price ({last_price:.2f}) is outside your filter.")
            
            df = analyze_new_logic(raw_df)
            
            # Filter Display Range
            mask = (df['Date'] >= st.session_state.test_start_date)
            final_view = df.loc[mask].copy()
            
            # Format
            final_view['Date'] = final_view['Date'].dt.strftime('%d-%b-%Y')
            
            # Separate Columns
            cols = ['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']
            final_view = final_view[cols]
            final_view.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            # Styling
            def color_rows(row):
                s = row['Type']
                if s == 'bull': return ['background-color: #C6EFCE; color: #006100; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear': return ['background-color: #FFC7CE; color: #9C0006; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if 'ATAK' in str(row['BU (Teji/Resist)']) or 'ATAK' in str(row['BE (Mandi/Support)']):
                     return ['background-color: #FFEB9C; color: #9C5700; font-weight: bold; white-space: pre-wrap;'] * len(row)
                return ['white-space: pre-wrap;'] * len(row)

            # RENDER
            st.dataframe(
                final_view.style.apply(color_rows, axis=1).format({
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                use_container_width=True,
                height=800,
                column_config={
                    "Type": None,
                    "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"),
                    "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")
                }
            )
            
        else: st.error("No data found.")
else:
    st.info("Select options and click Verify.")
