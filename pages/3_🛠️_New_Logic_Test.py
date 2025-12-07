import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.parse
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
    
    /* COLORS */
    .c-bull { background-color: #28a745; color: white; font-weight: bold; } /* Dark Green */
    .c-bear { background-color: #dc3545; color: white; font-weight: bold; } /* Dark Red */
    .c-bull-light { background-color: #d4edda; color: #155724; font-weight: bold; } /* Light Green */
    .c-bear-light { background-color: #f8d7da; color: #721c24; font-weight: bold; } /* Light Red */
    
    /* Sidebar text fix */
    .stSidebar label { color: #333 !important; }
    
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
        req_start = start - timedelta(days=60) # Buffer
        df = yf.download(yf_symbol, start=req_start, progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- 🛠️ NEW LOGIC (LOOK BACK FIX) ---
def analyze_new_logic(df):
    df['BU_Txt'], df['BU_Cls'] = "", ""
    df['BE_Txt'], df['BE_Cls'] = "", ""
    
    trend = "Neutral"
    
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    reaction_support = df.iloc[0]['Low']
    reaction_resist = df.iloc[0]['High']
    
    last_peak_idx = 0
    last_trough_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_h, c_l = curr['High'], curr['Low']
        date_str = curr['Date'].strftime('%d-%b').upper()
        
        # TEJI (Up)
        if trend == "Teji":
            if c_h > last_peak:
                # Mark NEW HIGH (Teji)
                df.at[i, 'BU_Txt'] = f"BU(T) {date_str}\n{c_h:.2f}"
                df.at[i, 'BU_Cls'] = "c-bull"
                
                # REACTION: Find lowest low between old peak and new peak
                swing_df = df.iloc[last_peak_idx:i+1]
                reaction_support = swing_df['Low'].min()
                
                # Mark Reaction Support (Light Green)
                df.at[i, 'BE_Txt'] = f"R(Teji)\n{reaction_support:.2f}"
                df.at[i, 'BE_Cls'] = "c-bull-light"
                
                last_peak = c_h
                last_peak_idx = i
                
            elif c_l < reaction_support:
                # 3. Support Broken -> Look Back for ATAK
                interim_df = df.iloc[last_peak_idx+1 : i]
                if not interim_df.empty:
                    atak_idx = interim_df['High'].idxmax()
                    atak_val = interim_df.loc[atak_idx, 'High']
                    
                    # Mark past row as ATAK (Top) - Light Red
                    df.at[atak_idx, 'BU_Txt'] = f"ATAK (Top)\n{atak_val:.2f}"
                    df.at[atak_idx, 'BU_Cls'] = "c-bear-light"
                
                # Mark Today as MANDI (Dark Red)
                trend = "Mandi"
                df.at[i, 'BE_Txt'] = f"BE(M) {date_str}\n{c_l:.2f}"
                df.at[i, 'BE_Cls'] = "c-bear"
                
                last_trough = c_l; last_trough_idx = i
                reaction_resist = c_h # Reset

        # MANDI (Down)
        elif trend == "Mandi":
            if c_l < last_trough:
                # Mark NEW LOW (Mandi)
                df.at[i, 'BE_Txt'] = f"BE(M) {date_str}\n{c_l:.2f}"
                df.at[i, 'BE_Cls'] = "c-bear"
                
                # REACTION: Find highest high between old trough and new trough
                swing_df = df.iloc[last_trough_idx:i+1]
                reaction_resist = swing_df['High'].max()
                
                # Mark Reaction Resistance (Light Red)
                df.at[i, 'BU_Txt'] = f"R(Mandi)\n{reaction_resist:.2f}"
                df.at[i, 'BU_Cls'] = "c-bear-light"
                
                last_trough = c_l; last_trough_idx = i
                
            elif c_h > reaction_resist:
                # 3. Resistance Broken -> Look Back for ATAK
                interim_df = df.iloc[last_trough_idx+1 : i]
                if not interim_df.empty:
                    atak_idx = interim_df['Low'].idxmin()
                    atak_val = interim_df.loc[atak_idx, 'Low']
                    
                    # Mark past row as ATAK (Bottom) - Light Green
                    df.at[atak_idx, 'BE_Txt'] = f"ATAK (Bot)\n{atak_val:.2f}"
                    df.at[atak_idx, 'BE_Cls'] = "c-bull-light"
                
                # Mark Today as TEJI (Dark Green)
                trend = "Teji"
                df.at[i, 'BU_Txt'] = f"BU(T) {date_str}\n{c_h:.2f}"
                df.at[i, 'BU_Cls'] = "c-bull"
                
                last_peak = c_h; last_peak_idx = i
                reaction_support = c_l # Reset

        # STARTUP
        else:
            if c_h > last_peak:
                trend = "Teji"; df.at[i, 'BU_Txt'] = "Start Teji"; df.at[i, 'BU_Cls']="c-bull"
                last_peak=c_h; last_peak_idx=i; reaction_support=df.iloc[i-1]['Low']
            elif c_l < last_trough:
                trend = "Mandi"; df.at[i, 'BE_Txt'] = "Start Mandi"; df.at[i, 'BE_Cls']="c-bear"
                last_trough=c_l; last_trough_idx=i; reaction_resist=df.iloc[i-1]['High']

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
            
            # HTML Render for safe layout
            html = """
            <table class="excel-table">
                <thead>
                    <tr>
                        <th width="15%">Date</th>
                        <th width="20%">High<br><span style='font-size:0.8em; font-weight:normal;'>Low</span></th>
                        <th width="20%">Open<br><span style='font-size:0.8em; font-weight:normal;'>Close</span></th>
                        <th width="22%">BU (Teji / Resist)</th>
                        <th width="22%">BE (Mandi / Support)</th>
                    </tr>
                </thead>
                <tbody>
            """
            for _, row in final_view.iterrows():
                d = row['Date'].strftime('%d-%b-%Y')
                hl = f"<div class='val-top'>{row['High']:.2f}</div><div class='val-bot'>{row['Low']:.2f}</div>"
                oc = f"<div class='val-top'>{row['Open']:.2f}</div><div class='val-bot'>{row['Close']:.2f}</div>"
                
                # Check empty cells
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
            
        else: st.error("No data found.")
else:
    st.info("Select options and click Verify.")
