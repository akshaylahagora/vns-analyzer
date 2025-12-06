import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS (NEW COLORS) ---
st.markdown("""
<style>
    /* Force Light Mode */
    .stApp { background-color: white; color: black; }
    
    /* VISIBILITY FIXES */
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; font-weight: 600 !important; }
    
    /* TABLE TEXT SIZE */
    .stDataFrame { font-size: 1.1rem; }
    .stSidebar label { color: #333 !important; }
    
    /* METRIC CARD CONTAINER */
    .metric-container {
        background-color: #f8f9fa;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
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
        req_start = start - timedelta(days=60)
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- NEW VNS LOGIC (UPDATED COLORS) ---
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
                # MARK TEJI (T) -> DARK GREEN
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull_dark"
                
                # REACTION -> LIGHT GREEN
                swing_df = df.iloc[last_peak_idx:i+1]
                reaction_support = swing_df['Low'].min()
                
                df.at[i, 'BE'] = f"R(Teji)\n{reaction_support:.2f}"
                # Note: We mark Reaction on the same line usually as info
                # But for color, if this row is BU(T), it's dark green. 
                # If we want distinct colors per cell, Pandas Styler handles it.
                
                last_peak = c_high; last_peak_idx = i
                
            elif c_low < reaction_support:
                # ATAK (TOP) -> LIGHT RED
                df.at[i, 'BU'] = f"ATAK (Top)\n{last_peak:.2f}"
                
                # MANDI (M) -> DARK RED
                trend = "Mandi"
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear_dark"
                
                last_trough = c_low; last_trough_idx = i
                reaction_resist = c_high

        # MANDI (Down)
        elif trend == "Mandi":
            if c_low < last_trough:
                # MARK MANDI (M) -> DARK RED
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_low:.2f}"
                df.at[i, 'Type'] = "bear_dark"
                
                # REACTION -> LIGHT RED
                swing_df = df.iloc[last_trough_idx:i+1]
                reaction_resist = swing_df['High'].max()
                
                df.at[i, 'BU'] = f"R(Mandi)\n{reaction_resist:.2f}"
                
                last_trough = c_low; last_trough_idx = i
                
            elif c_high > reaction_resist:
                # ATAK (BOTTOM) -> LIGHT GREEN
                df.at[i, 'BE'] = f"ATAK (Bot)\n{last_trough:.2f}"
                
                # TEJI (T) -> DARK GREEN
                trend = "Teji"
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_high:.2f}"
                df.at[i, 'Type'] = "bull_dark"
                
                last_peak = c_high; last_peak_idx = i
                reaction_support = c_low

        # NEUTRAL
        else:
            if c_high > last_peak:
                trend = "Teji"; df.at[i, 'BU'] = "Start Teji"; df.at[i, 'Type']="bull_dark"
                last_peak=c_high; last_peak_idx=i; reaction_support=df.iloc[i-1]['Low']
            elif c_low < last_trough:
                trend = "Mandi"; df.at[i, 'BE'] = "Start Mandi"; df.at[i, 'Type']="bear_dark"
                last_trough=c_low; last_trough_idx=i; reaction_resist=df.iloc[i-1]['High']
            
    return df, trend, reaction_resist, reaction_support

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            # Run logic on full data
            df_full, final_trend, fin_res, fin_sup = analyze_vns(raw_df)
            
            # Filter for display
            mask = (df_full['Date'] >= st.session_state.start_date) & (df_full['Date'] <= st.session_state.end_date)
            df = df_full.loc[mask].copy()
            
            # HEADER
            c1, c2, c3, c4 = st.columns(4)
            def card(label, value): return f"""<div class="metric-container"><div style="font-size:0.9rem; color:#666; font-weight:bold;">{label}</div><div style="font-size:1.6rem; color:#000; font-weight:bold;">{value}</div></div>"""
            with c1:
                # Custom Trend Badge
                color = "#28a745" if final_trend == "Teji" else "#dc3545" if final_trend == "Mandi" else "#6c757d"
                txt = "BULLISH (TEJI)" if final_trend == "Teji" else "BEARISH (MANDI)" if final_trend == "Mandi" else "NEUTRAL"
                st.markdown(f"""<div style="background:{color}; padding:15px; border-radius:8px; text-align:center; color:white; font-weight:bold; font-size:1.2rem;">{txt}</div>""", unsafe_allow_html=True)
            with c2: st.markdown(card("Last Close", f"{df.iloc[-1]['Close']:.2f}"), unsafe_allow_html=True)
            with c3: st.markdown(card("Active Resist", f"{fin_res:.2f}"), unsafe_allow_html=True)
            with c4: st.markdown(card("Active Support", f"{fin_sup:.2f}"), unsafe_allow_html=True)
            
            st.divider()
            
            # TABLE
            disp = df[['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']].copy()
            disp.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            # --- COLOR FUNCTION ---
            def color_cells(row):
                # Default background white
                styles = ['background-color: white; color: black; white-space: pre-wrap;'] * len(row)
                
                # Check BU Column
                bu_txt = str(row['BU (Teji/Resist)'])
                if "BU(T)" in bu_txt or "Teji" in bu_txt:
                    # Dark Green (New High)
                    styles[5] = 'background-color: #28a745; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in bu_txt:
                    # Light Red (Reaction of Mandi)
                    styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;'
                elif "ATAK" in bu_txt:
                    # Light Red (Atak Top)
                    styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;'

                # Check BE Column
                be_txt = str(row['BE (Mandi/Support)'])
                if "BE(M)" in be_txt or "Mandi" in be_txt:
                    # Dark Red (New Low)
                    styles[6] = 'background-color: #dc3545; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in be_txt:
                    # Light Green (Reaction of Teji)
                    styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;'
                elif "ATAK" in be_txt:
                    # Light Green (Atak Bottom)
                    styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;'
                
                return styles

            st.dataframe(
                disp.style.apply(color_cells, axis=1).format({
                    "Date": lambda t: t.strftime("%d-%b-%Y"),
                    "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"
                }),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")
