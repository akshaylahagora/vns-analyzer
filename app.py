import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS (EXCEL STYLING) ---
st.markdown("""
<style>
    /* Global Clean */
    .stApp { background-color: #ffffff; color: #000; }
    
    /* VNS Table Styling */
    .vns-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Arial', sans-serif;
        font-size: 14px;
        margin-top: 20px;
    }
    
    .vns-table th {
        background-color: #4472C4; /* Excel Blue Header */
        color: white;
        padding: 12px;
        text-align: center;
        border: 1px solid #8EA9DB;
    }
    
    .vns-table td {
        padding: 8px;
        text-align: center;
        border: 1px solid #d0d7e5;
        vertical-align: middle;
        line-height: 1.4;
    }
    
    /* Value Stacking */
    .val-top { font-weight: bold; color: #000; font-size: 1.1em; display: block; }
    .val-bot { color: #555; font-size: 0.95em; display: block; margin-top: 3px; }
    .lbl { font-size: 0.75em; color: #999; font-weight: normal; }

    /* --- EXCEL CONDITIONAL FORMATTING COLORS --- */
    
    /* TEJI (Good/Bullish) - Light Green BG, Dark Green Text */
    .c-bull { background-color: #C6EFCE; color: #006100; font-weight: bold; }
    
    /* MANDI (Bad/Bearish) - Light Red BG, Dark Red Text */
    .c-bear { background-color: #FFC7CE; color: #9C0006; font-weight: bold; }
    
    /* REACTION/NEUTRAL - Light Blue BG, Dark Blue Text */
    .c-info { background-color: #DDEBF7; color: #1F4E78; font-style: italic; }
    
    /* ATAK/WARNING - Light Yellow BG, Dark Yellow Text */
    .c-warn { background-color: #FFEB9C; color: #9C5700; font-weight: bold; }

</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
STOCK_LIST = ["RELIANCE", "HDFCBANK", "ICICIBANK", "INFY", "TCS", "ITC", "SBIN", "BHARTIARTL", "L&T", "AXISBANK", "KOTAKBANK", "HINDUNILVR", "TATAMOTORS", "MARUTI", "HCLTECH", "SUNPHARMA", "TITAN", "BAJFINANCE", "ULTRACEMCO", "ASIANPAINT", "NTPC", "POWERGRID", "M&M", "ADANIENT", "ADANIPORTS", "COALINDIA", "WIPRO", "BAJAJFINSV", "NESTLEIND", "JSWSTEEL", "GRASIM", "ONGC", "TATASTEEL", "HDFCLIFE", "SBILIFE", "DRREDDY", "EICHERMOT", "CIPLA", "DIVISLAB", "BPCL", "HINDALCO", "HEROMOTOCO", "APOLLOHOSP", "TATACONSUM", "BRITANNIA", "UPL", "ZOMATO", "PAYTM", "DLF", "INDIGO", "HAL", "BEL", "VBL", "TRENT", "JIOFIN", "ADANIPOWER", "IRFC", "PFC", "RECLTD", "BHEL"]
STOCK_LIST.sort()

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

# --- LOGIC ---
@st.cache_data(ttl=300)
def fetch_data(symbol, start, end):
    try:
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers); s.get("https://www.nseindia.com", timeout=5)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=10)
        if r.status_code == 200:
            df = pd.DataFrame(r.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE']: df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

def analyze_vns(df):
    # Initialize empty columns for CSS classes and Text
    df['BU_Txt'], df['BE_Txt'] = "", ""
    df['BU_Css'], df['BE_Css'] = "", ""
    
    trend = "Neutral"
    
    # We use index loop to look back
    for i in range(1, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        c_high, c_low, c_close = curr['CH_TRADE_HIGH_PRICE'], curr['CH_TRADE_LOW_PRICE'], curr['CH_CLOSING_PRICE']
        p_high, p_low = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        
        # Format date for the label (e.g., 6-NOV)
        d_lbl = prev['Date'].strftime('%-d-%b').upper()
        
        low_broken = c_low < p_low
        high_broken = c_high > p_high
        
        # --- STATE MACHINE ---
        if trend == "Bullish":
            # 1. Low Broken -> Top (BU)
            if low_broken:
                df.at[i-1, 'BU_Txt'] = f"BU(T) {d_lbl}<br>{p_high}"
                df.at[i-1, 'BU_Css'] = "c-bull"
            
            # 2. High Broken -> Reaction (BE)
            if high_broken:
                df.at[i-1, 'BE_Txt'] = f"R(Teji)<br>{p_low}"
                df.at[i-1, 'BE_Css'] = "c-info"

        elif trend == "Bearish":
            # 1. High Broken -> Bottom (BE)
            if high_broken:
                df.at[i-1, 'BE_Txt'] = f"BE(M) {d_lbl}<br>{p_low}"
                df.at[i-1, 'BE_Css'] = "c-bear"
                
            # 2. Low Broken -> Reaction (BU)
            if low_broken:
                df.at[i-1, 'BU_Txt'] = f"R(Mandi) {d_lbl}<br>{p_high}"
                df.at[i-1, 'BU_Css'] = "c-info"

        else: # Neutral
            if high_broken:
                trend = "Bullish"
                df.at[i-1, 'BE_Txt'] = f"Start Teji<br>{p_low}"
                df.at[i-1, 'BE_Css'] = "c-bull"
            elif low_broken:
                trend = "Bearish"
                df.at[i-1, 'BU_Txt'] = f"Start Mandi<br>{p_high}"
                df.at[i-1, 'BU_Css'] = "c-bear"
                
        # --- SWITCH CHECK ---
        # If we marked a BU in Bearish mode, and break it -> Switch
        if trend == "Bearish" and df.at[i-1, 'BU_Txt'] and c_close > p_high:
            trend = "Bullish"
            df.at[i, 'BU_Txt'] = "BREAKOUT<br>(Teji)"
            df.at[i, 'BU_Css'] = "c-bull"
            
        # If we marked a BE in Bullish mode, and break it -> Switch
        if trend == "Bullish" and df.at[i-1, 'BE_Txt'] and c_close < p_low:
            trend = "Bearish"
            df.at[i, 'BE_Txt'] = "BREAKDOWN<br>(Mandi)"
            df.at[i, 'BE_Css'] = "c-bear"

    return df

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df = analyze_vns(raw_df)
            
            # BUILD HTML STRING MANUALLY TO ENSURE FORMATTING
            html_rows = ""
            for _, r in df.iterrows():
                d = r['Date'].strftime('%d-%b-%Y')
                
                # Stacked Numbers
                hl = f"<span class='val-top'>{r['CH_TRADE_HIGH_PRICE']:.2f}</span><span class='val-bot'>{r['CH_TRADE_LOW_PRICE']:.2f}</span>"
                oc = f"<span class='val-top'>{r['CH_OPENING_PRICE']:.2f}</span><span class='val-bot'>{r['CH_CLOSING_PRICE']:.2f}</span>"
                
                html_rows += f"""
                <tr>
                    <td>{d}</td>
                    <td>{hl}</td>
                    <td>{oc}</td>
                    <td class="{r['BU_Css']}">{r['BU_Txt']}</td>
                    <td class="{r['BE_Css']}">{r['BE_Txt']}</td>
                </tr>
                """
            
            # FINAL TABLE HTML
            final_html = f"""
            <table class="vns-table">
                <thead>
                    <tr>
                        <th style="width:15%">Date</th>
                        <th style="width:20%">High<br><span class="lbl">Low</span></th>
                        <th style="width:20%">Open<br><span class="lbl">Close</span></th>
                        <th style="width:22%">BU (Resistance)</th>
                        <th style="width:22%">BE (Support)</th>
                    </tr>
                </thead>
                <tbody>
                    {html_rows}
                </tbody>
            </table>
            """
            
            # RENDER
            st.markdown(final_html, unsafe_allow_html=True)
            
        else: st.error("⚠️ Data Error")
else: st.info("👈 Click RUN")
