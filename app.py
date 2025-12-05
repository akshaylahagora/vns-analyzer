I have switched to a **Custom HTML Table**. This is the **only way** to guarantee that:

1.  **High is strictly above Low** (Stacked vertically, not side-by-side).
2.  **Headers are perfectly readable** (Dark text on light background).
3.  **Colors match Excel exactly** (High contrast).

### **Final Fixed Code: `Home.py`**

*Copy and replace your entire file. This version uses HTML rendering to force the layout you want.*

```python
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="VNS Pro Dashboard", page_icon="📈", layout="wide")

# --- CUSTOM CSS (EXCEL REPLICA) ---
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
    
    /* HEADER STYLES - High Readability */
    .excel-table th {
        background-color: #EFEFEF; /* Light Grey Header */
        color: #000000;            /* Black Text */
        font-weight: bold;
        border: 1px solid #BDBDBD;
        padding: 10px;
        text-align: center;
        vertical-align: middle;
    }
    
    /* CELL STYLES */
    .excel-table td {
        border: 1px solid #D0D0D0;
        padding: 6px 10px;
        text-align: center;
        vertical-align: middle;
    }
    
    /* STACKED DATA (High over Low) */
    .stack-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        line-height: 1.4;
    }
    .val-top { font-weight: bold; font-size: 1.1em; color: #000; }
    .val-bot { font-size: 1.0em; color: #555; }
    
    /* SIGNAL COLORS (Excel Standard) */
    .c-bull { background-color: #C6EFCE; color: #006100; font-weight: bold; } /* Green */
    .c-bear { background-color: #FFC7CE; color: #9C0006; font-weight: bold; } /* Red */
    .c-atak { background-color: #FFEB9C; color: #9C5700; font-weight: bold; } /* Yellow */
    .c-info { background-color: #E6F3FF; color: #000000; font-style: italic;} /* Blue */
    
    /* Sub-labels in header */
    .sub-head { font-size: 0.85em; color: #555; font-weight: normal; display: block; }

</style>
""", unsafe_allow_html=True)

# --- CONFIG ---
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

# --- DATA ---
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

# --- LOGIC ---
def analyze_vns(df):
    df['BU'], df['BE'] = "", ""
    df['BU_C'], df['BE_C'] = "", "" # Classes
    trend = "Neutral"
    
    last_bu, last_be = None, None
    
    for i in range(1, len(df)):
        curr = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = curr['CH_TRADE_HIGH_PRICE'], curr['CH_TRADE_LOW_PRICE'], curr['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        d_str = prev['Date'].strftime('%d-%b').upper()
        
        # ATAK
        if last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu:
            df.at[i, 'BU'] = f"ATAK (Top)<br>{c_h}"
            df.at[i, 'BU_C'] = "c-atak"
        if last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be:
            df.at[i, 'BE'] = f"ATAK (Bottom)<br>{c_l}"
            df.at[i, 'BE_C'] = "c-atak"

        # TREND
        if trend == "Bullish":
            if c_l < p_l: 
                df.at[i-1, 'BU'] = f"BU(T) {d_str}<br>{p_h}"
                df.at[i-1, 'BU_C'] = "c-bull"
                last_bu = p_h
            if c_h > p_h: 
                df.at[i-1, 'BE'] = f"R(Teji)<br>{p_l}"
                df.at[i-1, 'BE_C'] = "c-info"
                last_be = p_l
        
        elif trend == "Bearish":
            if c_h > p_h: 
                df.at[i-1, 'BE'] = f"BE(M) {d_str}<br>{p_l}"
                df.at[i-1, 'BE_C'] = "c-bear"
                last_be = p_l
            if c_l < p_l: 
                df.at[i-1, 'BU'] = f"R(Mandi) {d_str}<br>{p_h}"
                df.at[i-1, 'BU_C'] = "c-info"
                last_bu = p_h
                
        else: # Neutral
            if c_h > p_h: trend = "Bullish"; df.at[i-1, 'BE'] = f"Start Teji<br>{p_l}"; df.at[i-1, 'BE_C']="c-bull"; last_be = p_l
            elif c_l < p_l: trend = "Bearish"; df.at[i-1, 'BU'] = f"Start Mandi<br>{p_h}"; df.at[i-1, 'BU_C']="c-bear"; last_bu = p_h
            
        # SWITCH
        if trend == "Bearish" and last_bu and c_c > last_bu:
            trend = "Bullish"; df.at[i, 'BU'] = "BREAKOUT (Teji)"; df.at[i, 'BU_C']="c-bull"
        if trend == "Bullish" and last_be and c_c < last_be:
            trend = "Bearish"; df.at[i, 'BE'] = "BREAKDOWN (Mandi)"; df.at[i, 'BE_C']="c-bear"
            
    return df

# --- RENDER ---
st.title(f"📊 VNS Theory: {selected_stock}")
st.markdown(f"Analysis: **{st.session_state.start_date.strftime('%d-%b-%Y')}** to **{st.session_state.end_date.strftime('%d-%b-%Y')}**")

if run_btn:
    with st.spinner("Fetching..."):
        raw_df = fetch_data(selected_stock, st.session_state.start_date, st.session_state.end_date)
        if raw_df is not None:
            df = analyze_vns(raw_df)
            
            # --- HTML TABLE BUILDER ---
            html = """
            <table class="excel-table">
                <thead>
                    <tr>
                        <th width="15%">Date</th>
                        <th width="20%">High<br><span class="sub-head">Low</span></th>
                        <th width="20%">Open<br><span class="sub-head">Close</span></th>
                        <th width="22%">BU<br><span class="sub-head">Resistance</span></th>
                        <th width="22%">BE<br><span class="sub-head">Support</span></th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for _, row in df.iterrows():
                d = row['Date'].strftime('%d-%b-%Y')
                hl = f"<div class='stack-box'><span class='val-top'>{row['CH_TRADE_HIGH_PRICE']:.2f}</span><span class='val-bot'>{row['CH_TRADE_LOW_PRICE']:.2f}</span></div>"
                oc = f"<div class='stack-box'><span class='val-top'>{row['CH_OPENING_PRICE']:.2f}</span><span class='val-bot'>{row['CH_CLOSING_PRICE']:.2f}</span></div>"
                
                # Check for empty cells to maintain table structure
                bu_content = row['BU'] if row['BU'] else "&nbsp;"
                be_content = row['BE'] if row['BE'] else "&nbsp;"
                
                html += f"""
                <tr>
                    <td>{d}</td>
                    <td>{hl}</td>
                    <td>{oc}</td>
                    <td class="{row['BU_C']}">{bu_content}</td>
                    <td class="{row['BE_C']}">{be_content}</td>
                </tr>
                """
            html += "</tbody></table>"
            st.markdown(html, unsafe_allow_html=True)
        else: st.error("⚠️ Error fetching data.")
else: st.info("👈 Click RUN")
```
