import streamlit as st
import pandas as pd
import requests
import urllib.parse
import time
from datetime import datetime, timedelta

# --- PAGE CONFIG ---
st.set_page_config(page_title="Advanced Classifier", page_icon="⚡", layout="wide")

st.title("⚡ Advanced VNS Classifier")
st.markdown("Identifies **Breakouts**, **Trend Continuation**, and **Reversal Risks (Atak)**.")

# --- PRO CSS (HIGH CONTRAST & VISIBILITY) ---
st.markdown("""
<style>
    /* Force Light Mode for Readability */
    .stApp { background-color: #f0f2f6; color: #000000; }
    
    /* CARD DESIGN */
    .class-card {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.08);
        margin-bottom: 12px;
        border-left-width: 6px;
        border-left-style: solid;
        transition: transform 0.1s;
    }
    .class-card:hover { transform: scale(1.01); }
    
    /* TEXT STYLES */
    .stock-title { font-size: 1.2rem; font-weight: 800; color: #2c3e50; }
    .stock-price { font-size: 1.1rem; font-weight: 600; color: #333; }
    .signal-text { font-size: 0.9rem; font-weight: 600; margin-top: 5px; color: #555; }
    
    /* CHANGE BADGES */
    .chg-green { color: #008000; font-weight: bold; font-size: 0.9rem; }
    .chg-red { color: #d63031; font-weight: bold; font-size: 0.9rem; }
    
    /* BORDER COLORS (Classification) */
    .b-high-bull { border-left-color: #00b894; } /* Bright Green */
    .b-bull { border-left-color: #55efc4; }      /* Light Green */
    .b-high-bear { border-left-color: #d63031; } /* Bright Red */
    .b-bear { border-left-color: #fab1a0; }      /* Light Red */
    .b-atak-top { border-left-color: #e17055; }  /* Dark Orange */
    .b-atak-bot { border-left-color: #fdcb6e; }  /* Yellow */
    
    /* LINK BUTTON STYLE */
    .chart-link {
        text-decoration: none;
        font-size: 0.8rem;
        color: #0984e3;
        font-weight: bold;
        float: right;
        margin-top: 5px;
    }
    .chart-link:hover { text-decoration: underline; }

</style>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---
FNO_STOCKS = [
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
FNO_STOCKS = sorted(list(set(FNO_STOCKS)))

# --- SESSION STATE ---
if 'classified_results' not in st.session_state:
    st.session_state.classified_results = [] 

# --- CORE LOGIC ---
def fetch_stock_data(symbol):
    try:
        safe_symbol = urllib.parse.quote(symbol)
        end = datetime.now()
        start = end - timedelta(days=40) 
        
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        s = requests.Session(); s.headers.update(headers)
        s.get("https://www.nseindia.com", timeout=3)
        
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={safe_symbol}&type=priceVolumeDeliverable&series=ALL"
        r = s.get(url, timeout=5)
        
        if r.status_code == 200:
            df = pd.DataFrame(r.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE', 'CH_TRADE_LOW_PRICE', 'CH_OPENING_PRICE', 'CH_CLOSING_PRICE', 'CH_PREVIOUS_CLS_PRICE']: 
                df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None
    return None

def classify_stock(df):
    trend = "Neutral"
    last_bu, last_be = None, None
    signal_desc = "Neutral"
    category = "Neutral" 
    
    for i in range(1, len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1]
        c_h, c_l, c_c = row['CH_TRADE_HIGH_PRICE'], row['CH_TRADE_LOW_PRICE'], row['CH_CLOSING_PRICE']
        p_h, p_l = prev['CH_TRADE_HIGH_PRICE'], prev['CH_TRADE_LOW_PRICE']
        
        low_broken = c_l < p_l
        high_broken = c_h > p_h
        
        # ATAK Logic 
        is_atak_top = last_bu and (last_bu*0.995 <= c_h <= last_bu*1.005) and c_c < last_bu
        is_atak_bot = last_be and (last_be*0.995 <= c_l <= last_be*1.005) and c_c > last_be
        
        current_signal = ""
        
        if trend == "Bullish":
            if low_broken: last_bu = p_h; current_signal = "Top Made (BU)"
            if high_broken: last_be = p_l; current_signal = "Reaction Buy (Dip)"
            if is_atak_top: current_signal = "ATAK (Double Top)"
            
        elif trend == "Bearish":
            if high_broken: last_be = p_l; current_signal = "Bottom Made (BE)"
            if low_broken: last_bu = p_h; current_signal = "Reaction Sell (Rise)"
            if is_atak_bot: current_signal = "ATAK (Double Bottom)"
            
        else: # Neutral
            if high_broken: trend="Bullish"; last_be=p_l; current_signal="Trend Start (Bull)"
            elif low_broken: trend="Bearish"; last_bu=p_h; current_signal="Trend Start (Bear)"
            
        # Switch Logic
        if trend == "Bearish" and last_bu and c_c > last_bu:
            trend = "Bullish"; current_signal = "BREAKOUT (Fresh Teji)"
        if trend == "Bullish" and last_be and c_c < last_be:
            trend = "Bearish"; current_signal = "BREAKDOWN (Fresh Mandi)"
            
        # Final Classification
        if i == len(df) - 1:
            signal_desc = current_signal
            if "BREAKOUT" in current_signal: category = "Highly Bullish"
            elif "BREAKDOWN" in current_signal: category = "Highly Bearish"
            elif "ATAK (Double Top)" in current_signal: category = "Atak (Teji Side)"
            elif "ATAK (Double Bottom)" in current_signal: category = "Atak (Mandi Side)"
            elif trend == "Bullish": category = "Bullish"
            elif trend == "Bearish": category = "Bearish"

    # Calc % Change
    last_row = df.iloc[-1]
    pct_change = ((last_row['CH_CLOSING_PRICE'] - last_row['CH_PREVIOUS_CLS_PRICE']) / last_row['CH_PREVIOUS_CLS_PRICE']) * 100
    
    return category, signal_desc, last_row['CH_CLOSING_PRICE'], pct_change

# --- UI EXECUTION ---

if st.button("⚡ Start Advanced Classification Scan", type="primary"):
    results = []
    bar = st.progress(0)
    status = st.empty()
    
    for i, stock in enumerate(FNO_STOCKS):
        status.caption(f"Scanning {stock}...")
        df = fetch_stock_data(stock)
        
        if df is not None:
            cat, sig, close, chg = classify_stock(df)
            if close > 0: 
                results.append({ "Symbol": stock, "Price": close, "Change": chg, "Category": cat, "Signal": sig })
        
        bar.progress((i + 1) / len(FNO_STOCKS))
        time.sleep(0.1) 
        
    st.session_state.classified_results = results
    bar.empty(); status.empty()
    st.success("Scan Complete!")

# --- DISPLAY RESULTS ---

if st.session_state.classified_results:
    
    st.divider()
    search_query = st.text_input("🔍 Search Stock", placeholder="e.g. RELIANCE").upper()
    
    data = st.session_state.classified_results
    if search_query: data = [d for d in data if search_query in d['Symbol']]
        
    # Buckets
    high_bull = [d for d in data if d['Category'] == "Highly Bullish"]
    bull = [d for d in data if d['Category'] == "Bullish"]
    high_bear = [d for d in data if d['Category'] == "Highly Bearish"]
    bear = [d for d in data if d['Category'] == "Bearish"]
    atak_teji = [d for d in data if d['Category'] == "Atak (Teji Side)"]
    atak_mandi = [d for d in data if d['Category'] == "Atak (Mandi Side)"]
    
    # Render Function
    def render_category(title, items, border_class):
        with st.expander(f"{title} ({len(items)})", expanded=True):
            if not items: st.caption("No stocks found.")
            
            for item in items:
                # Color code % change
                chg_color = "chg-green" if item['Change'] >= 0 else "chg-red"
                chg_sign = "+" if item['Change'] >= 0 else ""
                
                # TradingView Link
                tv_link = f"https://in.tradingview.com/chart/?symbol=NSE:{item['Symbol']}"
                
                st.markdown(f"""
                <div class="class-card {border_class}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="stock-title">{item['Symbol']}</span>
                        <span class="stock-price">₹{item['Price']:.2f}</span>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
                        <span class="{chg_color}">{chg_sign}{item['Change']:.2f}%</span>
                        <a href="{tv_link}" target="_blank" class="chart-link">📈 Chart</a>
                    </div>
                    <div class="signal-text">Signal: {item['Signal']}</div>
                </div>
                """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    
    with c1:
        render_category("🚀 Highly Bullish (Breakout)", high_bull, "b-high-bull")
        render_category("🔴 Bearish (Trend)", bear, "b-bear")
        
    with c2:
        render_category("🟢 Bullish (Trend)", bull, "b-bull")
        render_category("⚠️ Atak on Teji (Top)", atak_teji, "b-atak-top")
        
    with c3:
        render_category("🩸 Highly Bearish (Breakdown)", high_bear, "b-high-bear")
        render_category("🛡️ Atak on Mandi (Bottom)", atak_mandi, "b-atak-bot")

else:
    st.info("Click the button above to scan.")
