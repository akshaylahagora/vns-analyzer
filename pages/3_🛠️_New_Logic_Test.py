import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Logic Test", page_icon="🛠️", layout="wide")

st.title("🛠️ New VNS Logic Test")
st.markdown("Testing logic: **Higher Highs (BU/T)**, **Lower Lows (BE/M)**, and **Reactions (R)**.")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* Sidebar Label Color */
    .stSidebar label { color: #333 !important; }
    
    /* Table Styling */
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    
    /* Radio Button Tabs */
    div[role="radiogroup"] { flex-wrap: wrap; gap: 5px; }
    div[role="radiogroup"] > label { 
        border: 1px solid #ccc; 
        background: #f8f9fa;
        padding: 5px 10px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# --- COMPLETE STOCK LIST (180+) ---
STOCK_LIST = [
    "360ONE", "ABB", "APLAPOLLO", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", 
    "ABCAPITAL", "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", 
    "ASTRAL", "AUROPHARMA", "DMART", "AXISBANK", "BSE", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", 
    "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHEL", "BPCL", 
    "BHARTIARTL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BRITANNIA", "CGPOWER", "CANBK", "CDSL", 
    "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CAMS", "CONCOR", "CROMPTON", 
    "CUMMINSIND", "CYIENT", "DLF", "DABUR", "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", 
    "DRREDDY", "EICHERMOT", "EXIDEIND", "NYKAA", "FORTIS", "GAIL", "GMRAIRPORT", "GLENMARK", 
    "GODREJCP", "GODREJPROP", "GRASIM", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL", 
    "HAVELLS", "HEROMOTOCO", "HINDALCO", "HAL", "HINDPETRO", "HINDUNILVR", "HINDZINC", "POWERINDIA", 
    "HUDCO", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IIFL", "ITC", "INDIANB", "IEX", 
    "IOC", "IRCTC", "IRFC", "IREDA", "INDUSTOWER", "INDUSINDBK", "NAUKRI", "INFY", "INOXWIND", 
    "INDIGO", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JIOFIN", "JUBLFOOD", "KEI", "KPITTECH", 
    "KALYANKJIL", "KAYNES", "KFINTECH", "KOTAKBANK", "LTF", "LICHSGFIN", "LTIM", "LT", "LAURUSLABS", 
    "LICI", "LODHA", "LUPIN", "M&M", "MANAPPURAM", "MANKIND", "MARICO", "MARUTI", "MFSL", 
    "MAXHEALTH", "MAZDOCK", "MPHASIS", "MCX", "MUTHOOTFIN", "NBCC", "NCC", "NHPC", "NMDC", 
    "NTPC", "NATIONALUM", "NESTLEIND", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", "OFSS", 
    "POLICYBZR", "PGEL", "PIIND", "PNBHOUSING", "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", 
    "PIDILITIND", "PPLPHARMA", "POLYCAB", "PFC", "POWERGRID", "PRESTIGE", "PNB", "RBLBANK", 
    "RECLTD", "RVNL", "RELIANCE", "SBICARD", "SBILIFE", "SHREECEM", "SRF", "SAMMAANCAP", 
    "MOTHERSON", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", "SBIN", "SAIL", "SUNPHARMA", 
    "SUPREMEIND", "SUZLON", "SYNGENE", "TATACONSUM", "TITAGARH", "TVSMOTOR", "TCS", "TATAELXSI", 
    "TATAPOWER", "TATASTEEL", "TATATECH", "TECHM", "FEDERALBNK", "INDHOTEL", "PHOENIXLTD", 
    "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TIINDIA", "UNOMINDA", "UPL", "ULTRACEMCO", 
    "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "IDEA", "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
]
STOCK_LIST = sorted(list(set(STOCK_LIST))) 

# --- STATE ---
if 'test_start_date' not in st.session_state: st.session_state.test_start_date = datetime.now() - timedelta(days=60)
if 'test_duration_label' not in st.session_state: st.session_state.test_duration_label = "2M"

def update_dates():
    sel = st.session_state.duration_select
    st.session_state.test_duration_label = sel
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
    period_sel = st.radio("Duration", ["1M", "2M", "3M", "6M", "1Y", "Custom"], index=1, horizontal=True, key="duration_select", on_change=update_dates)
    
    if period_sel == "Custom":
        c_dates = st.date_input("Range", (st.session_state.test_start_date, datetime.now()))
        if len(c_dates) == 2: st.session_state.test_start_date = datetime.combine(c_dates[0], datetime.min.time())
    
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
        req_start = start - timedelta(days=30)
        df = yf.download(yf_symbol, start=req_start, progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- 🛠️ NEW LOGIC (MATCHING EXCEL FORMAT) ---
def analyze_new_logic(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    reaction_support = df.iloc[0]['Low']
    reaction_resist = df.iloc[0]['High']
    
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_high, c_low = curr['High'], curr['Low']
        date_str = curr['Date'].strftime('%d-%b').upper()
        
        # TEJI (Up)
        if trend == "Teji":
            if c_high > last_peak:
                # Mark NEW HIGH (Teji)
                df.at[i, 'BU'] = f"BU(T) {date_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                
                # Find Reaction Low
                swing_df = df.iloc[last_peak_idx:i+1]
                reaction_support = swing_df['Low'].min()
                
                df.at[i, 'BE'] = f"R(Reaction of Teji)\n{reaction_support:.2f}"
                df.at[i, 'Type'] = "info"
                
                last_peak = c_high
                last_peak_idx = i
                
            elif c_low < reaction_support:
                # Broken Support -> ATAK Top
                df.at[i, 'BU'] = f"ATAK (Top)\n{last_peak:.2f}"
                
                trend = "Mandi"
                df.at[i, 'BE'] = f"BE(M) {date_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                
                last_trough = c_low
                last_trough_idx = i
                reaction_resist = c_high

        # MANDI (Down)
        elif trend == "Mandi":
            if c_low < last_trough:
                # Mark NEW LOW (Mandi)
                df.at[i, 'BE'] = f"BE(M) {date_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                
                # Find Reaction High
                swing_df = df.iloc[last_trough_idx:i+1]
                reaction_resist = swing_df['High'].max()
                
                df.at[i, 'BU'] = f"R(Reaction of Mandi)\n{reaction_resist:.2f}"
                df.at[i, 'Type'] = "info"
                
                last_trough = c_low
                last_trough_idx = i
                
            elif c_high > reaction_resist:
                # Broken Resist -> ATAK Bottom
                df.at[i, 'BE'] = f"ATAK (Bot)\n{last_trough:.2f}"
                
                trend = "Teji"
                df.at[i, 'BU'] = f"BU(T) {date_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                
                last_peak = c_high
                last_peak_idx = i
                reaction_support = c_low

        # STARTUP
        else:
            if c_high > last_peak:
                trend = "Teji"
                df.at[i, 'BU'] = f"Start Teji\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                last_peak = c_high; last_peak_idx = i
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
                st.warning(f"⚠️ Stock Price ({last_price:.2f}) is outside your filter ({min_p}-{max_p}), but showing data anyway.")
            
            df = analyze_new_logic(raw_df)
            
            # Filter Display Range
            mask = (df['Date'] >= st.session_state.test_start_date)
            final_view = df.loc[mask].copy()
            
            # Formatting Date
            final_view['Date'] = final_view['Date'].dt.strftime('%d-%b-%Y')
            
            # Select Columns
            cols = ['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']
            final_view = final_view[cols]
            final_view.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (High is Higher)', 'BE (Low is Lower)', 'Type']
            
            # Styling
            def color_rows(row):
                s = row['Type']
                if s == 'bull': return ['background-color: #C6EFCE; color: #006100; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear': return ['background-color: #FFC7CE; color: #9C0006; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'info': return ['background-color: #E6F3FF; color: #000; font-style: italic; white-space: pre-wrap;'] * len(row)
                if 'ATAK' in str(row['BU (High is Higher)']) or 'ATAK' in str(row['BE (Low is Lower)']):
                     return ['background-color: #FFEB9C; color: #9C5700; font-weight: bold; white-space: pre-wrap;'] * len(row)
                return ['white-space: pre-wrap;'] * len(row)

            # RENDER TABLE
            st.dataframe(
                final_view.style.apply(color_rows, axis=1).format({
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                use_container_width=True,
                height=800,
                column_config={
                    "Type": None,
                    "BU (High is Higher)": st.column_config.TextColumn(width="medium"),
                    "BE (Low is Lower)": st.column_config.TextColumn(width="medium")
                }
            )
            
        else: st.error("No data found.")
else:
    st.info("Select options and click Verify.")
