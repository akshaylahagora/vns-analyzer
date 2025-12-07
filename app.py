import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    div[data-testid="stMetricValue"] { color: #000000 !important; }
    
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; border: 2px solid transparent; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
    
    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .metric-container { background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- STOCK LIST ---
STOCK_LIST = [
    "360ONE", "ABB", "APLAPOLLO", "AUBANK", "ADANIENSOL", "ADANIENT", "ADANIGREEN", "ADANIPORTS", "ABCAPITAL", "ALKEM", "AMBER", "AMBUJACEM", "ANGELONE", "APOLLOHOSP", "ASHOKLEY", "ASIANPAINT", "ASTRAL", "AUROPHARMA", "DMART", "AXISBANK", "BSE", "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BANDHANBNK", "BANKBARODA", "BANKINDIA", "BDL", "BEL", "BHARATFORG", "BHEL", "BPCL", "BHARTIARTL", "BIOCON", "BLUESTARCO", "BOSCHLTD", "BRITANNIA", "CGPOWER", "CANBK", "CDSL", "CHOLAFIN", "CIPLA", "COALINDIA", "COFORGE", "COLPAL", "CAMS", "CONCOR", "CROMPTON", "CUMMINSIND", "CYIENT", "DLF", "DABUR", "DALBHARAT", "DELHIVERY", "DIVISLAB", "DIXON", "DRREDDY", "EICHERMOT", "EXIDEIND", "NYKAA", "FORTIS", "GAIL", "GMRAIRPORT", "GLENMARK", "GODREJCP", "GODREJPROP", "GRASIM", "HCLTECH", "HDFCAMC", "HDFCBANK", "HDFCLIFE", "HFCL", "HAVELLS", "HEROMOTOCO", "HINDALCO", "HAL", "HINDPETRO", "HINDUNILVR", "HINDZINC", "POWERINDIA", "HUDCO", "ICICIBANK", "ICICIGI", "ICICIPRULI", "IDFCFIRSTB", "IIFL", "ITC", "INDIANB", "IEX", "IOC", "IRCTC", "IRFC", "IREDA", "INDUSTOWER", "INDUSINDBK", "NAUKRI", "INFY", "INOXWIND", "INDIGO", "JINDALSTEL", "JSWENERGY", "JSWSTEEL", "JIOFIN", "JUBLFOOD", "KEI", "KPITTECH", "KALYANKJIL", "KAYNES", "KFINTECH", "KOTAKBANK", "LTF", "LICHSGFIN", "LTIM", "LT", "LAURUSLABS", "LICI", "LODHA", "LUPIN", "M&M", "MANAPPURAM", "MANKIND", "MARICO", "MARUTI", "MFSL", "MAXHEALTH", "MAZDOCK", "MPHASIS", "MCX", "MUTHOOTFIN", "NBCC", "NCC", "NHPC", "NMDC", "NTPC", "NATIONALUM", "NESTLEIND", "NUVAMA", "OBEROIRLTY", "ONGC", "OIL", "PAYTM", "OFSS", "POLICYBZR", "PGEL", "PIIND", "PNBHOUSING", "PAGEIND", "PATANJALI", "PERSISTENT", "PETRONET", "PIDILITIND", "PPLPHARMA", "POLYCAB", "PFC", "POWERGRID", "PRESTIGE", "PNB", "RBLBANK", "RECLTD", "RVNL", "RELIANCE", "SBICARD", "SBILIFE", "SHREECEM", "SRF", "SAMMAANCAP", "MOTHERSON", "SHRIRAMFIN", "SIEMENS", "SOLARINDS", "SONACOMS", "SBIN", "SAIL", "SUNPHARMA", "SUPREMEIND", "SUZLON", "SYNGENE", "TATACONSUM", "TITAGARH", "TVSMOTOR", "TCS", "TATAELXSI", "TATAPOWER", "TATASTEEL", "TATATECH", "TECHM", "FEDERALBNK", "INDHOTEL", "PHOENIXLTD", "TITAN", "TORNTPHARM", "TORNTPOWER", "TRENT", "TIINDIA", "UNOMINDA", "UPL", "ULTRACEMCO", "UNIONBANK", "UNITDSPR", "VBL", "VEDL", "IDEA", "VOLTAS", "WIPRO", "YESBANK", "ZYDUSLIFE"
]
STOCK_LIST = sorted(list(set(STOCK_LIST))) 

# --- STATE ---
if 'start_date' not in st.session_state: st.session_state.start_date = datetime.now() - timedelta(days=60)
if 'end_date' not in st.session_state: st.session_state.end_date = datetime.now()

def update_dates():
    sel = st.session_state.duration_selector
    now = datetime.now()
    days = {"1M":30, "2M":60, "3M":90, "6M":180, "1Y":365}
    if sel == "YTD": st.session_state.start_date = datetime(now.year, 1, 1)
    elif sel in days: st.session_state.start_date = now - timedelta(days=days[sel])
    st.session_state.end_date = now

with st.sidebar:
    st.header("⚙️ Settings")
    selected_stock = st.selectbox("Select Stock", STOCK_LIST, index=STOCK_LIST.index("KOTAKBANK") if "KOTAKBANK" in STOCK_LIST else 0)
    st.divider()
    st.radio("Period:", ["1M", "2M", "3M", "6M", "1Y", "YTD", "Custom"], index=1, horizontal=True, key="duration_selector", on_change=update_dates)
    date_range = st.date_input("Range", (st.session_state.start_date, st.session_state.end_date))
    if len(date_range) == 2: st.session_state.start_date, st.session_state.end_date = [datetime.combine(d, datetime.min.time()) for d in date_range]
    st.divider()
    run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# --- FETCH ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start - timedelta(days=60)
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- VNS LOGIC (Break Low/High to Mark) ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    # Track Major Tops/Bottoms
    last_major_top = df.iloc[0]['High']
    last_major_bot = df.iloc[0]['Low']
    
    # Track "Reaction" levels (Swings inside a trend)
    reaction_high = df.iloc[0]['High']
    reaction_low = df.iloc[0]['Low']
    
    # Indices to find swigs
    start_search_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        c_h, c_l, c_c = curr['High'], curr['Low'], curr['Close']
        p_h, p_l = prev['High'], prev['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # 1. LOW BROKEN -> MARK A TOP (BU)
        if c_l < p_l:
            # Find the highest point since the last marked event
            swing_df = df.iloc[start_search_idx : i]
            if not swing_df.empty:
                max_idx = swing_df['High'].idxmax()
                max_val = df.at[max_idx, 'High']
                
                # Check Logic
                bu_label = ""
                bu_type = ""
                
                if trend == "Teji":
                    if max_val >= last_major_top:
                        bu_label = f"BU(T) {d_str}\n{max_val:.2f}"; bu_type = "bull_dark" # Continuation
                        last_major_top = max_val
                    else:
                        bu_label = f"ATAK (Top)\n{max_val:.2f}"; bu_type = "bear_light" # Failed Top
                        # Atak in Teji implies potential reversal
                
                elif trend == "Mandi":
                    # In Mandi, a new top is a Reaction
                    bu_label = f"R (Mandi)\n{max_val:.2f}"; bu_type = "bear_light"
                    reaction_high = max_val
                
                else: # Neutral
                    if max_val > last_major_top:
                        trend = "Teji"
                        bu_label = f"Start Teji\n{max_val:.2f}"; bu_type = "bull_dark"
                        last_major_top = max_val
                
                # Apply Mark
                df.at[max_idx, 'BU'] = bu_label
                df.at[max_idx, 'Type'] = bu_type
                
                # Check for Breakout (Trend Change to Teji)
                if trend == "Mandi" and max_val > reaction_high:
                     # This logic is usually handled on the crossing day, handled below
                     pass
                
                start_search_idx = i # Reset search

        # 2. HIGH BROKEN -> MARK A BOTTOM (BE)
        if c_h > p_h:
            # Find the lowest point since the last marked event
            swing_df = df.iloc[start_search_idx : i]
            if not swing_df.empty:
                min_idx = swing_df['Low'].idxmin()
                min_val = df.at[min_idx, 'Low']
                
                be_label = ""
                be_type = ""
                
                if trend == "Mandi":
                    if min_val <= last_major_bot:
                        be_label = f"BE(M) {d_str}\n{min_val:.2f}"; be_type = "bear_dark" # Continuation
                        last_major_bot = min_val
                    else:
                        be_label = f"ATAK (Bot)\n{min_val:.2f}"; be_type = "bull_light" # Failed Bottom
                
                elif trend == "Teji":
                    # In Teji, a new low is a Reaction
                    be_label = f"R (Teji)\n{min_val:.2f}"; be_type = "bull_light"
                    reaction_low = min_val
                    
                else: # Neutral
                     if min_val < last_major_bot:
                        trend = "Mandi"
                        be_label = f"Start Mandi\n{min_val:.2f}"; be_type = "bear_dark"
                        last_major_bot = min_val
                
                # Apply Mark
                df.at[min_idx, 'BE'] = be_label
                df.at[min_idx, 'Type'] = be_type
                
                start_search_idx = i

        # 3. BREAKOUT / BREAKDOWN CHECKS (Trend Flipping)
        # Teji -> Mandi (Break Reaction Low)
        if trend == "Teji" and c_c < reaction_low:
             trend = "Mandi"
             df.at[i, 'BE'] = f"BREAKDOWN\n{c_c:.2f}"
             df.at[i, 'Type'] = "bear_dark"
             last_major_bot = c_l # Start tracking new low
             
        # Mandi -> Teji (Break Reaction High)
        if trend == "Mandi" and c_c > reaction_high:
             trend = "Teji"
             df.at[i, 'BU'] = f"BREAKOUT\n{c_c:.2f}"
             df.at[i, 'Type'] = "bull_dark"
             last_major_top = c_h

    # Return active levels
    fin_res = reaction_high if trend == "Mandi" else last_major_top
    fin_sup = reaction_low if trend == "Teji" else last_major_bot
    
    return df, trend, fin_res, fin_sup

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df_full, final_trend, fin_res, fin_sup = analyze_vns(raw_df)
            mask = (df_full['Date'] >= st.session_state.start_date) & (df_full['Date'] <= st.session_state.end_date)
            df = df_full.loc[mask].copy()
            
            c1, c2, c3, c4 = st.columns(4)
            def card(label, value): return f"""<div class="metric-container"><div style="font-size:0.9rem; color:#666; font-weight:bold;">{label}</div><div style="font-size:1.6rem; color:#000; font-weight:bold;">{value}</div></div>"""
            with c1:
                color, txt = ("#6c757d", "NEUTRAL")
                if final_trend == "Teji": color, txt = ("#d1e7dd", "BULLISH (TEJI)")
                elif final_trend == "Mandi": color, txt = ("#f8d7da", "BEARISH (MANDI)")
                st.markdown(f"""<div style="background:{color}; padding:15px; border-radius:8px; text-align:center; color:black; font-weight:bold; font-size:1.2rem; border:1px solid #ccc;">{txt}</div>""", unsafe_allow_html=True)
            with c2: st.markdown(card("Last Close", f"{df.iloc[-1]['Close']:.2f}"), unsafe_allow_html=True)
            with c3: st.markdown(card("Active Resist", f"{fin_res:.2f}"), unsafe_allow_html=True)
            with c4: st.markdown(card("Active Support", f"{fin_sup:.2f}"), unsafe_allow_html=True)
            
            st.divider()
            
            disp = df[['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']].copy()
            disp.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            def color_cells(row):
                styles = ['background-color: white; color: black; white-space: pre-wrap;'] * len(row)
                bu_txt = str(row['BU (Teji/Resist)'])
                be_txt = str(row['BE (Mandi/Support)'])
                
                # BU
                if "BU(T)" in bu_txt or "Start Teji" in bu_txt or "BREAKOUT" in bu_txt:
                    styles[5] = 'background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in bu_txt or "ATAK" in bu_txt:
                    styles[5] = 'background-color: #f8d7da; color: black; font-weight: bold; white-space: pre-wrap;'

                # BE
                if "BE(M)" in be_txt or "Start Mandi" in be_txt or "BREAKDOWN" in be_txt:
                    styles[6] = 'background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;'
                elif "R(" in be_txt or "ATAK" in be_txt:
                    styles[6] = 'background-color: #d4edda; color: black; font-weight: bold; white-space: pre-wrap;'
                
                return styles

            st.dataframe(
                disp.style.apply(color_cells, axis=1).format({"Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")