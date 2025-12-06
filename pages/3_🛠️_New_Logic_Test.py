import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Logic Test", page_icon="🛠️", layout="wide")

st.title("🛠️ New VNS Logic Test")
st.markdown("Testing new rules: **Higher Highs (Teji)**, **Lower Lows (Mandi)**, and **Reaction Point Reversals (Atak)**.")

# --- CUSTOM CSS (MATCHING HOME.PY) ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* TABLE STYLES */
    .excel-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 14px;
        color: #000;
        margin-bottom: 50px;
    }
    
    .excel-table th {
        background-color: #EFEFEF;
        color: #000000;
        font-weight: bold;
        border: 1px solid #BDBDBD;
        padding: 10px;
        text-align: center;
        vertical-align: middle;
    }
    
    .excel-table td {
        border: 1px solid #D0D0D0;
        padding: 6px 10px;
        text-align: center;
        vertical-align: middle;
    }
    
    /* STACKED DATA */
    .val-top { font-weight: bold; font-size: 1.1em; color: #000; display: block; }
    .val-bot { font-size: 1.0em; color: #555; display: block; margin-top: 2px; }
    .sub-head { font-size: 0.85em; color: #555; font-weight: normal; display: block; }
    
    /* COLORS */
    .c-bull { background-color: #C6EFCE; color: #006100; font-weight: bold; } /* Green */
    .c-bear { background-color: #FFC7CE; color: #9C0006; font-weight: bold; } /* Red */
    .c-atak { background-color: #FFEB9C; color: #9C5700; font-weight: bold; } /* Yellow */
    .c-info { background-color: #E6F3FF; color: #000000; font-style: italic;} /* Blue */
    
    /* Sidebar text fix */
    .stSidebar label { color: #333 !important; }
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
if 'test_start_date' not in st.session_state: st.session_state.test_start_date = datetime.now() - timedelta(days=90)

with st.sidebar:
    st.header("⚙️ Test Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    
    date_range = st.date_input("Range", (st.session_state.test_start_date, datetime.now()))
    if len(date_range) == 2: 
        start_d, end_d = [datetime.combine(d, datetime.min.time()) for d in date_range]
    else:
        start_d, end_d = st.session_state.test_start_date, datetime.now()
        
    run_btn = st.button("🚀 Verify New Logic", type="primary", use_container_width=True)

# --- DATA FETCHING (YAHOO FINANCE) ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        # Fetch extra history for trend calculation
        req_start = start - timedelta(days=60) 
        
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False)
        
        if df.empty: return None
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Filter back to requested range for display, but keep history for logic if needed
        # For simplicity in this test script, we process everything we fetched
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- 🛠️ NEW VNS LOGIC ---
def analyze_new_logic(df):
    df['BU_Txt'], df['BU_Cls'] = "", ""
    df['BE_Txt'], df['BE_Cls'] = "", ""
    
    trend = "Neutral"
    
    # State tracking
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    reaction_support = df.iloc[0]['Low']
    reaction_resist = df.iloc[0]['High']
    
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_high, c_low = curr['High'], curr['Low']
        
        # --- TEJI (UPTREND) LOGIC ---
        if trend == "Teji":
            # 1. Higher High? (Trend Continue)
            if c_high > last_peak:
                # Mark NEW HIGH as Teji
                df.at[i, 'BU_Txt'] = f"T (Teji)\n{c_high:.2f}"
                df.at[i, 'BU_Cls'] = "c-bull"
                
                # FIND REACTION LOW (Lowest between prev peak and current peak)
                swing_df = df.iloc[last_peak_idx:i+1] 
                lowest_in_swing = swing_df['Low'].min()
                reaction_support = lowest_in_swing
                
                # Mark Reaction
                df.at[i, 'BE_Txt'] = f"R (Support)\n{reaction_support:.2f}"
                df.at[i, 'BE_Cls'] = "c-info"
                
                last_peak = c_high
                last_peak_idx = i
                
            # 2. Reaction Support Broken? (Trend Reversal -> Mandi)
            elif c_low < reaction_support:
                # Previous Peak becomes ATAK (Top)
                df.at[i, 'BU_Txt'] = f"ATAK (Top)\n{last_peak:.2f}"
                df.at[i, 'BU_Cls'] = "c-atak"
                
                # This Low becomes MANDI (Bottom)
                trend = "Mandi"
                df.at[i, 'BE_Txt'] = f"M (Mandi)\n{c_low:.2f}"
                df.at[i, 'BE_Cls'] = "c-bear"
                
                last_trough = c_low
                last_trough_idx = i
                reaction_resist = c_high # Init resistance for new trend

        # --- MANDI (DOWNTREND) LOGIC ---
        elif trend == "Mandi":
            # 1. Lower Low? (Trend Continue)
            if c_low < last_trough:
                # Mark NEW LOW as Mandi
                df.at[i, 'BE_Txt'] = f"M (Mandi)\n{c_low:.2f}"
                df.at[i, 'BE_Cls'] = "c-bear"
                
                # FIND REACTION HIGH (Highest between prev trough and current trough)
                swing_df = df.iloc[last_trough_idx:i+1]
                highest_in_swing = swing_df['High'].max()
                reaction_resist = highest_in_swing
                
                # Mark Reaction
                df.at[i, 'BU_Txt'] = f"R (Resist)\n{reaction_resist:.2f}"
                df.at[i, 'BU_Cls'] = "c-info"
                
                last_trough = c_low
                last_trough_idx = i
                
            # 2. Reaction Resistance Broken? (Trend Reversal -> Teji)
            elif c_high > reaction_resist:
                # Previous Trough becomes ATAK (Bottom)
                df.at[i, 'BE_Txt'] = f"ATAK (Bot)\n{last_trough:.2f}"
                df.at[i, 'BE_Cls'] = "c-atak"
                
                # This High becomes TEJI (Top)
                trend = "Teji"
                df.at[i, 'BU_Txt'] = f"T (Teji)\n{c_high:.2f}"
                df.at[i, 'BU_Cls'] = "c-bull"
                
                last_peak = c_high
                last_peak_idx = i
                reaction_support = c_low # Init support for new trend

        # --- NEUTRAL / STARTUP ---
        else:
            if c_high > last_peak:
                trend = "Teji"
                df.at[i, 'BU_Txt'] = "Start Teji"
                df.at[i, 'BU_Cls'] = "c-bull"
                last_peak = c_high
                last_peak_idx = i
                reaction_support = df.iloc[i-1]['Low']
            elif c_low < last_trough:
                trend = "Mandi"
                df.at[i, 'BE_Txt'] = "Start Mandi"
                df.at[i, 'BE_Cls'] = "c-bear"
                last_trough = c_low
                last_trough_idx = i
                reaction_resist = df.iloc[i-1]['High']

    return df

# --- RENDER ---
if run_btn:
    with st.spinner(f"Testing new logic on {selected_stock}..."):
        raw_df = fetch_data(selected_stock, start_d, end_d)
        
        if raw_df is not None:
            # Filter to show only requested range in table, but logic ran on full fetch
            df = analyze_new_logic(raw_df)
            mask = (df['Date'] >= start_d) & (df['Date'] <= end_d)
            display_df = df.loc[mask]
            
            # HTML Render
            html = """
            <table class="excel-table">
                <thead>
                    <tr>
                        <th width="15%">Date</th>
                        <th width="20%">High<br><span class="sub-head">Low</span></th>
                        <th width="20%">Open<br><span class="sub-head">Close</span></th>
                        <th width="22%">BU (Teji / Resist)</th>
                        <th width="22%">BE (Mandi / Support)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for _, row in display_df.iterrows():
                d = row['Date'].strftime('%d-%b-%Y')
                hl = f"<div class='stack-box'><span class='val-top'>{row['High']:.2f}</span><span class='val-bot'>{row['Low']:.2f}</span></div>"
                oc = f"<div class='stack-box'><span class='val-top'>{row['Open']:.2f}</span><span class='val-bot'>{row['Close']:.2f}</span></div>"
                
                bu = row['BU_Txt'] if row['BU_Txt'] else ""
                be = row['BE_Txt'] if row['BE_Txt'] else ""
                
                html += f"""
                <tr>
                    <td>{d}</td>
                    <td>{hl}</td>
                    <td>{oc}</td>
                    <td class="{row['BU_Cls']}">{bu}</td>
                    <td class="{row['BE_Cls']}">{be}</td>
                </tr>
                """
            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)
            
        else:
            st.error("No data found or connection failed.")
else:
    st.info("Select a stock and date range, then click 'Verify New Logic'.")
