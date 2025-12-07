import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Logic Test", page_icon="🛠️", layout="wide")

st.title("🛠️ New VNS Logic Test")
st.markdown("Testing new rules: **Higher Highs (Teji)**, **Reaction Breakdowns (Atak/Mandi)**.")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .stSidebar label { color: #333 !important; }
    div[role="radiogroup"] > label { border: 1px solid #ccc; background: #f8f9fa; padding: 5px 10px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
STOCK_LIST = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"]
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
    st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y", "Custom"], index=1, horizontal=True, key="duration_select", on_change=update_dates)
    
    if st.session_state.duration_select == "Custom":
        c_dates = st.date_input("Range", (st.session_state.test_start_date, datetime.now()))
        if len(c_dates) == 2: st.session_state.test_start_date = datetime.combine(c_dates[0], datetime.min.time())
        
    st.divider()
    min_p = st.number_input("Min Price", 0, value=1000)
    max_p = st.number_input("Max Price", 0, value=100000)
    st.divider()
    run_btn = st.button("🚀 Verify New Logic", type="primary", use_container_width=True)

# --- DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start - timedelta(days=60)
        df = yf.download(yf_symbol, start=req_start, progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- 🛠️ REFINED LOGIC (Bounce Detection) ---
def analyze_new_logic(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    # Trackers
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    # Reaction Tracking (Dynamic)
    swing_low = df.iloc[0]['Low'] # For Teji -> Mandi
    swing_high = df.iloc[0]['High'] # For Mandi -> Teji
    
    swing_low_idx = 0
    swing_high_idx = 0
    
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_h, c_l = curr['High'], curr['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- TEJI (UPTREND) ---
        if trend == "Teji":
            # 1. Continuation (New High)
            if c_h > last_peak:
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"; df.at[i, 'Type'] = "bull_dark"
                
                # Mark previous swing low as the Confirmed Reaction
                # (Logic: The low between old peak and new peak is the reaction)
                if last_peak_idx < swing_low_idx < i:
                    df.at[swing_low_idx, 'BE'] = f"R(Teji)\n{swing_low:.2f}"
                    df.at[swing_low_idx, 'Type'] = "bull_light"

                last_peak = c_h; last_peak_idx = i
                swing_low = c_l; swing_low_idx = i # Reset swing low tracking
                
            else:
                # Track the lowest low since peak (Potential Reaction)
                if c_l < swing_low:
                    swing_low = c_l; swing_low_idx = i
                    
                # 2. Reversal Check (Break Reaction Low)
                # Logic: If we drop below 'swing_low', AND we had a bounce before this drop?
                # Your example: 20th High -> 21st Low -> 23rd Lower High -> 24th Break.
                
                # We need to check if there was a "Lower High" (Bounce) between Swing Low and Current.
                # Look at data between swing_low_idx and current i
                if i > swing_low_idx:
                    bounce_df = df.iloc[swing_low_idx+1 : i]
                    if not bounce_df.empty:
                        bounce_high = bounce_df['High'].max()
                        bounce_idx = bounce_df['High'].idxmax()
                        
                        # If current low breaks the swing low
                        if c_l < swing_low:
                            # 1. Mark the Bounce High as ATAK
                            df.at[bounce_idx, 'BU'] = f"ATAK (Top)\n{bounce_high:.2f}"
                            df.at[bounce_idx, 'Type'] = "bear_light"
                            
                            # 2. Mark Previous Low as Reaction (if not marked)
                            df.at[swing_low_idx, 'BE'] = f"R(Teji)\n{swing_low:.2f}"
                            df.at[swing_low_idx, 'Type'] = "bull_light"
                            
                            # 3. Mark Today as MANDI
                            df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"
                            df.at[i, 'Type'] = "bear_dark"
                            
                            trend = "Mandi"
                            last_trough = c_l; last_trough_idx = i
                            swing_high = c_h; swing_high_idx = i # Start tracking high for Mandi

        # --- MANDI (DOWNTREND) ---
        elif trend == "Mandi":
            # 1. Continuation (New Low)
            if c_l < last_trough:
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"; df.at[i, 'Type'] = "bear_dark"
                
                # Mark previous swing high as Reaction
                if last_trough_idx < swing_high_idx < i:
                    df.at[swing_high_idx, 'BU'] = f"R(Mandi)\n{swing_high:.2f}"
                    df.at[swing_high_idx, 'Type'] = "bear_light"

                last_trough = c_l; last_trough_idx = i
                swing_high = c_h; swing_high_idx = i
                
            else:
                # Track highest high since trough
                if c_h > swing_high:
                    swing_high = c_h; swing_high_idx = i
                    
                # 2. Reversal Check (Break Reaction High)
                if i > swing_high_idx:
                    dip_df = df.iloc[swing_high_idx+1 : i]
                    if not dip_df.empty:
                        dip_low = dip_df['Low'].min()
                        dip_idx = dip_df['Low'].idxmin()
                        
                        if c_h > swing_high:
                            # 1. Mark Dip Low as ATAK
                            df.at[dip_idx, 'BE'] = f"ATAK (Bot)\n{dip_low:.2f}"
                            df.at[dip_idx, 'Type'] = "bull_light"
                            
                            # 2. Mark Prev High as Reaction
                            df.at[swing_high_idx, 'BU'] = f"R(Mandi)\n{swing_high:.2f}"
                            df.at[swing_high_idx, 'Type'] = "bear_light"
                            
                            # 3. Mark Today as TEJI
                            df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"
                            df.at[i, 'Type'] = "bull_dark"
                            
                            trend = "Teji"
                            last_peak = c_h; last_peak_idx = i
                            swing_low = c_l; swing_low_idx = i

        # --- NEUTRAL ---
        else:
            if c_h > last_peak:
                trend = "Teji"; df.at[i, 'BU'] = "Start Teji"; df.at[i, 'Type']="bull_dark"
                last_peak=c_h; last_peak_idx=i; swing_low=c_l; swing_low_idx=i
            elif c_l < last_trough:
                trend = "Mandi"; df.at[i, 'BE'] = "Start Mandi"; df.at[i, 'Type']="bear_dark"
                last_trough=c_l; last_trough_idx=i; swing_high=c_h; swing_high_idx=i

    return df

# --- RENDER ---
if run_btn:
    with st.spinner(f"Fetching {selected_stock}..."):
        raw_df = fetch_data(selected_stock, st.session_state.test_start_date)
        if raw_df is not None:
            df = analyze_new_logic(raw_df)
            mask = (df['Date'] >= st.session_state.test_start_date)
            final_view = df.loc[mask].copy()
            
            # Format
            cols = ['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']
            final_view = final_view[cols]
            final_view.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            # Colors
            def color_rows(row):
                s = row['Type']
                if s == 'bull_dark': return ['background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear_dark': return ['background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bull_light': return ['background-color: #d4edda; color: black; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear_light': return ['background-color: #FFC0CB; color: black; font-weight: bold; white-space: pre-wrap;'] * len(row)
                return ['white-space: pre-wrap;'] * len(row)

            st.dataframe(
                final_view.style.apply(color_rows, axis=1).format({"Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
                use_container_width=True, height=800,
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")}
            )
        else: st.error("No data found.")
else: st.info("Select options and click Verify.")
