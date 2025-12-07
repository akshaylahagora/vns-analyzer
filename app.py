import streamlit as st
import pandas as pd
import requests
import urllib.parse
from datetime import datetime, timedelta
import yfinance as yf

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .stApp { background-color: white; color: black; }
    
    div[data-testid="stMetricValue"] { color: #000000 !important; font-size: 1.6rem !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; font-weight: 600 !important; }
    
    .trend-card { padding: 15px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 1.2rem; border: 2px solid transparent; }
    .trend-bull { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
    .trend-bear { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; }
    .trend-neutral { background-color: #e2e3e5; color: #41464b; border-color: #d3d6d8; }

    .stDataFrame { font-size: 1.1rem; }
    .stDataFrame td { vertical-align: middle !important; white-space: pre-wrap !important; }
    .metric-container { background-color: #f8f9fa; border: 1px solid #ddd; border-radius: 8px; padding: 15px; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
STOCK_LIST = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"]
STOCK_LIST.sort()

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

# --- FETCH ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        yf_symbol = f"{symbol}.NS"
        req_start = start - timedelta(days=60) # Buffer
        df = yf.download(yf_symbol, start=req_start, end=end + timedelta(days=1), progress=False, auto_adjust=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={'Date': 'Date', 'Open': 'Open', 'High': 'High', 'Low': 'Low', 'Close': 'Close'})
        df['Date'] = pd.to_datetime(df['Date'])
        return df.sort_values('Date').reset_index(drop=True)
    except: return None

# --- VNS LOGIC ENGINE (STRICT CONFIRMED LEVELS) ---
def analyze_vns(df):
    df['BU'], df['BE'], df['Type'] = "", "", ""
    trend = "Neutral"
    
    # Current Active Levels (The stop loss lines)
    active_support = None
    active_resistance = None
    
    # Tracking Levels (For calculating next support/resist)
    last_peak = df.iloc[0]['High']
    last_trough = df.iloc[0]['Low']
    
    # Indices for lookback
    last_peak_idx = 0
    last_trough_idx = 0
    
    # To track where the active support/resist was established
    support_idx = 0
    resist_idx = 0
    
    for i in range(1, len(df)):
        curr = df.iloc[i]
        c_h, c_l = curr['High'], curr['Low']
        d_str = curr['Date'].strftime('%d-%b').upper()
        
        # --- TEJI (UPTREND) ---
        if trend == "Teji":
            # 1. New High? (Continuation)
            if c_h > last_peak:
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"
                df.at[i, 'Type'] = "bull_dark"
                
                # The lowest low between Old Peak and New Peak becomes the NEW Active Support
                swing_df = df.iloc[last_peak_idx : i+1]
                min_idx = swing_df['Low'].idxmin()
                active_support = df.at[min_idx, 'Low']
                support_idx = min_idx
                
                # Mark Reaction (Past)
                r_date = df.at[min_idx, 'Date'].strftime('%d-%b').upper()
                df.at[min_idx, 'BE'] = f"R(Teji) {r_date}\n{active_support:.2f}"
                if df.at[min_idx, 'Type'] == "": df.at[min_idx, 'Type'] = "bull_light"
                
                last_peak = c_h
                last_peak_idx = i
            
            # 2. Support Broken? (Reversal)
            elif active_support is not None and c_l < active_support:
                # LOOK BACK: Highest point between Support Date and Today is ATAK
                # Range: support_idx + 1 to i
                if i > support_idx:
                    interim = df.iloc[support_idx+1 : i]
                    if not interim.empty:
                        atak_idx = interim['High'].idxmax()
                        atak_val = df.at[atak_idx, 'High']
                        a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                        
                        df.at[atak_idx, 'BU'] = f"ATAK (Top) {a_date}\n{atak_val:.2f}"
                        df.at[atak_idx, 'Type'] = "bear_light"
                
                # Mark Today as Mandi Start
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"
                df.at[i, 'Type'] = "bear_dark"
                
                trend = "Mandi"
                last_trough = c_l
                last_trough_idx = i
                active_resistance = c_h # Init resistance at breakdown high
                resist_idx = i

        # --- MANDI (DOWNTREND) ---
        elif trend == "Mandi":
            # 1. New Low? (Continuation)
            if c_l < last_trough:
                df.at[i, 'BE'] = f"BE(M) {d_str}\n{c_l:.2f}"
                df.at[i, 'Type'] = "bear_dark"
                
                # The highest high between Old Trough and New Trough becomes NEW Active Resistance
                swing_df = df.iloc[last_trough_idx : i+1]
                max_idx = swing_df['High'].idxmax()
                active_resistance = df.at[max_idx, 'High']
                resist_idx = max_idx
                
                # Mark Reaction (Past)
                r_date = df.at[max_idx, 'Date'].strftime('%d-%b').upper()
                df.at[max_idx, 'BU'] = f"R(Mandi) {r_date}\n{active_resistance:.2f}"
                if df.at[max_idx, 'Type'] == "": df.at[max_idx, 'Type'] = "bear_light"
                
                last_trough = c_l
                last_trough_idx = i
            
            # 2. Resistance Broken? (Reversal)
            elif active_resistance is not None and c_h > active_resistance:
                # LOOK BACK: Lowest point between Resistance Date and Today is ATAK
                if i > resist_idx:
                    interim = df.iloc[resist_idx+1 : i]
                    if not interim.empty:
                        atak_idx = interim['Low'].idxmin()
                        atak_val = df.at[atak_idx, 'Low']
                        a_date = df.at[atak_idx, 'Date'].strftime('%d-%b').upper()
                        
                        df.at[atak_idx, 'BE'] = f"ATAK (Bot) {a_date}\n{atak_val:.2f}"
                        df.at[atak_idx, 'Type'] = "bull_light"
                
                # Mark Today as Teji Start
                df.at[i, 'BU'] = f"BU(T) {d_str}\n{c_h:.2f}"
                df.at[i, 'Type'] = "bull_dark"
                
                trend = "Teji"
                last_peak = c_h
                last_peak_idx = i
                active_support = c_l # Init support at breakout low
                support_idx = i

        # --- NEUTRAL ---
        else:
            if c_h > last_peak:
                trend = "Teji"; df.at[i, 'BU'] = "Start Teji"; df.at[i, 'Type']="bull_dark"
                last_peak=c_h; last_peak_idx=i; active_support=df.iloc[i-1]['Low']; support_idx=i-1
            elif c_l < last_trough:
                trend = "Mandi"; df.at[i, 'BE'] = "Start Mandi"; df.at[i, 'Type']="bear_dark"
                last_trough=c_l; last_trough_idx=i; active_resistance=df.iloc[i-1]['High']; resist_idx=i-1

    return df, trend, active_resistance, active_support

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
            
            # Display logic for Active Levels
            res_disp = f"{fin_res:.2f}" if final_trend == "Mandi" and fin_res else "-"
            sup_disp = f"{fin_sup:.2f}" if final_trend == "Teji" and fin_sup else "-"
            
            with c3: st.markdown(card("Active Resist", res_disp), unsafe_allow_html=True)
            with c4: st.markdown(card("Active Support", sup_disp), unsafe_allow_html=True)
            
            st.divider()
            
            disp = df[['Date', 'Open', 'High', 'Low', 'Close', 'BU', 'BE', 'Type']].copy()
            disp.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'BU (Teji/Resist)', 'BE (Mandi/Support)', 'Type']
            
            def color_cells(row):
                styles = ['background-color: white; color: black; white-space: pre-wrap;'] * len(row)
                bu_txt = str(row['BU (Teji/Resist)'])
                be_txt = str(row['BE (Mandi/Support)'])

                # BU Column
                if "BU(T)" in bu_txt or "Start Teji" in bu_txt:
                    styles[5] = 'background-color: #228B22; color: white; font-weight: bold; white-space: pre-wrap;' # Dark Green
                elif "R(" in bu_txt:
                    styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;' # Light Red
                elif "ATAK" in bu_txt:
                    styles[5] = 'background-color: #f8d7da; color: #721c24; font-weight: bold; white-space: pre-wrap;' # Light Red

                # BE Column
                if "BE(M)" in be_txt or "Start Mandi" in be_txt:
                    styles[6] = 'background-color: #8B0000; color: white; font-weight: bold; white-space: pre-wrap;' # Dark Red
                elif "R(" in be_txt:
                    styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;' # Light Green
                elif "ATAK" in be_txt:
                    styles[6] = 'background-color: #d4edda; color: #155724; font-weight: bold; white-space: pre-wrap;' # Light Green
                
                return styles

            st.dataframe(
                disp.style.apply(color_cells, axis=1).format({"Date": lambda t: t.strftime("%d-%b-%Y"), "Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "Close": "{:.2f}"}),
                column_config={"Type": None, "BU (Teji/Resist)": st.column_config.TextColumn(width="medium"), "BE (Mandi/Support)": st.column_config.TextColumn(width="medium")},
                use_container_width=True, height=800
            )
        else: st.error("⚠️ Data Error.")
else: st.info("👈 Click RUN")