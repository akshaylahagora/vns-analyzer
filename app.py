import streamlit as st
import pandas as pd
import yfinance as yf
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    /* Header Cards */
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-label { font-size: 0.9rem; font-weight: 600; color: #666; text-transform: uppercase; }
    .metric-value { font-size: 1.6rem; font-weight: 700; color: #000; }
    
    /* Trend Badges */
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border: 2px solid #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border: 2px solid #f5c2c7; }
    .trend-neutral { background-color: #e2e3e5; color: #41464b; border: 2px solid #d3d6d8; }

    /* Table */
    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    
    .stSidebar label { color: #333 !important; }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
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
if 'start_date' not in st.session_state: st.session_state.start_date = datetime.now() - timedelta(days=60)
if 'end_date' not in st.session_state: st.session_state.end_date = datetime.now()

def update_dates():
    sel = st.session_state.duration_selector
    now = datetime.now()
    st.session_state.end_date = now
    days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)
    elif sel in days: st.session_state.start_date = now - timedelta(days=days[sel])

with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.radio("Period:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Range", (st.session_state.start_date, st.session_state.end_date))
    if len(date_range) == 2: st.session_state.start_date, st.session_state.end_date = [datetime.combine(d, datetime.min.time()) for d in date_range]
    st.divider()
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# --- DATA ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        # Fetch extra history for calculation context (important for finding swing points)
        req_start = start - timedelta(days=60)
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- NEW VNS LOGIC ---
def analyze_vns(df):
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
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # TEJI (Up)
        if trend == "Teji":
            if c_high > last_peak:
                # Continuation: Higher High
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull"
                
                # Reaction: Lowest Low in swing
                swing_df = df.iloc[last_peak_idx:i+1]
                reaction_support = swing_df['Low'].min()
                
                df.at[i, 'BE'] = f"R (Reaction of Teji)\n{reaction_support:.2f}"
                df.at[i, 'Type'] = "info"
                
                last_peak = c_high; last_peak_idx = i
                
            elif c_low < reaction_support:
                # Reversal: Break Support -> Atak/Mandi
                df.at[i, 'BU'] = f"ATAK (Top)\n{last_peak:.2f}"
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "warn" # Mark breakdown row as warn/bear
                
                trend = "Mandi"
                last_trough = c_low; last_trough_idx = i
                reaction_resist = c_high

        # MANDI (Down)
        elif trend == "Mandi":
            if c_low < last_trough:
                # Continuation: Lower Low
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear"
                
                # Reaction: Highest High in swing
                swing_df = df.iloc[last_trough_idx:i+1]
                reaction_resist = swing_df['High'].max()
                
                df.at[i, 'BU'] = f"R (Reaction of Mandi)\n{reaction_resist:.2f}"
                df.at[i, 'Type'] = "info"
                
                last_trough = c_low; last_trough_idx = i
                
            elif c_high > reaction_resist:
                # Reversal: Break Resist -> Atak/Teji
                df.at[i, 'BE'] = f"ATAK (Bot)\n{last_trough:.2f}"
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "warn"
                
                trend = "Teji"
                last_peak = c_high; last_peak_idx = i
                reaction_support = c_low

        # NEUTRAL
        else:
            if c_high > last_peak:
                trend = "Teji"; df.at[i, 'BU'] = "Start Teji"; df.at[i, 'Type']="bull"
                last_peak=c_high; last_peak_idx=i; reaction_support=df.iloc[i-1]['Low']
            elif c_low < last_trough:
                trend = "Mandi"; df.at[i, 'BE'] = "Start Mandi"; df.at[i, 'Type']="bear"
                last_trough=c_low; last_trough_idx=i; reaction_resist=df.iloc[i-1]['High']
            
    return df, trend, reaction_resist, reaction_support

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            # Run logic on full data, then filter for display
            df_full, final_trend, fin_res, fin_sup = analyze_vns(raw_df)
            
            mask = (df_full['Date'] >= st.session_state.start_date) & (df_full['Date'] <= st.session_state.end_date)
            df = df_full.loc[mask].copy()
            
            # HEADER
            c1, c2, c3, c4 = st.columns(4)
            def card(label, value): return f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>"""
            with c1:
                cls, txt = ("trend-neutral", "NEUTRAL")
                if final_trend == "Teji": cls, txt = ("trend-bull", "BULLISH (TEJI)")
                elif final_trend == "Mandi": cls, txt = ("trend-bear", "BEARISH (MANDI)")
                st.markdown(f"""<div class="trend-card {cls}"><div style="font-size:0.8rem; margin-bottom:5px;">OVERALL TREND</div>{txt}</div>""", unsafe_allow_html=True)
            with c2: st.markdown(card("Last Close", f"{df.iloc[-1]['Close']:.2f}"), unsafe_allow_html=True)
            with c3: st.markdown(card("Active Resist", f"{fin_res:.2f}"), unsafe_allow_html=True)
            with c4: st.markdown(card("Active Support", f"{fin_sup:.2f}"), unsafe_allow_html=True)
            
            st.divider()
            
            # TABLE
            disp = df[['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']].copy()
            disp.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            def color_rows(row):
                s = row['Type']
                if s == 'bull': return ['background-color: #C6EFCE; color: #006100; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'bear': return ['background-color: #FFC7CE; color: #9C0006; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'warn': return ['background-color: #FFEB9C; color: #9C5700; font-weight: bold; white-space: pre-wrap;'] * len(row)
                if s == 'info': return ['background-color: #E6F3FF; color: #000; font-style: italic; white-space: pre-wrap;'] * len(row)
                return ['white-space: pre-wrap;'] * len(row)

            st.dataframe(
                disp.style.apply(color_rows, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")
