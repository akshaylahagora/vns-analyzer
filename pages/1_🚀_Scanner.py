import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="F&O Scanner", page_icon="🔭", layout="wide")
st.title("🔭 F&O VNS Scanner (> ₹1000)")
st.markdown("Scanning major F&O stocks (Last 30 Days Data)")

st.markdown("""
<style>
    .scan-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ddd; }
    .bull-box { background-color: #d4edda; border-color: #c3e6cb; color: #155724; }
    .bear-box { background-color: #f8d7da; border-color: #f5c6cb; color: #721c24; }
    .metric-val { font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# SAMPLE F&O LIST (>1000 typically)
FNO_STOCKS = [
    "RELIANCE", "HDFCBANK", "INFY", "TCS", "KOTAKBANK", "LT", "AXISBANK", "SBIN", 
    "BAJFINANCE", "TITAN", "ULTRACEMCO", "MARUTI", "ASIANPAINT", "HINDUNILVR", "M&M", 
    "ADANIENT", "GRASIM", "BAJAJFINSV", "NESTLEIND", "EICHERMOT", "DRREDDY", "DIVISLAB", 
    "APOLLOHOSP", "BRITANNIA", "TRENT", "HAL", "BEL", "SIEMENS", "INDIGO", "TATASTEEL", 
    "JIOFIN", "COALINDIA", "HCLTECH", "SUNPHARMA", "ADANIPORTS", "WIPRO"
]

@st.cache_data(ttl=600)
def fetch_stock_data(symbol):
    try:
        end = datetime.now(); start = end - timedelta(days=40)
        headers = { "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/" }
        session = requests.Session(); session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=3)
        url = f"https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from={start.strftime('%d-%m-%Y')}&to={end.strftime('%d-%m-%Y')}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL"
        response = session.get(url, timeout=5)
        if response.status_code == 200:
            df = pd.DataFrame(response.json().get('data', []))
            if df.empty: return None
            df = df[df['CH_SERIES'] == 'EQ']
            df['Date'] = pd.to_datetime(df['mTIMESTAMP'])
            for c in ['CH_TRADE_HIGH_PRICE','CH_TRADE_LOW_PRICE','CH_OPENING_PRICE','CH_CLOSING_PRICE']: df[c] = df[c].astype(float)
            return df.sort_values('Date').reset_index(drop=True)
    except: return None

def get_trend(df):
    trend = "Neutral"; bu, be = None, None
    for i in range(len(df)):
        row = df.iloc[i]; prev = df.iloc[i-1] if i > 0 else None
        if prev is not None:
            if row['CH_TRADE_LOW_PRICE'] < prev['CH_TRADE_LOW_PRICE']: bu = prev['CH_TRADE_HIGH_PRICE']
            if row['CH_TRADE_HIGH_PRICE'] > prev['CH_TRADE_HIGH_PRICE']: be = prev['CH_TRADE_LOW_PRICE']
            if bu and row['CH_CLOSING_PRICE'] > bu: trend = "Bullish"
            elif be and row['CH_CLOSING_PRICE'] < be: trend = "Bearish"
    return trend, bu, be, df.iloc[-1]['CH_CLOSING_PRICE']

if st.button("🚀 Start Scan"):
    results = []; bar = st.progress(0); txt = st.empty()
    for i, stock in enumerate(FNO_STOCKS):
        txt.text(f"Scanning {stock}...")
        df = fetch_stock_data(stock)
        if df is not None:
            if df.iloc[-1]['CH_CLOSING_PRICE'] > 1000:
                tr, bu, be, cl = get_trend(df)
                results.append({"Sym": stock, "Trend": tr, "Close": cl, "BU": bu, "BE": be, "Data": df})
        bar.progress((i+1)/len(FNO_STOCKS)); time.sleep(0.1)
    
    bar.empty(); txt.empty()
    bulls = [r for r in results if r['Trend'] == "Bullish"]
    bears = [r for r in results if r['Trend'] == "Bearish"]
    
    c1, c2 = st.columns(2)
    with c1:
        st.header(f"🟢 Bullish ({len(bulls)})")
        for s in bulls:
            with st.expander(f"{s['Sym']} (₹{s['Close']:.2f})"):
                st.markdown(f"<div class='scan-box bull-box'><b>TEJI</b><br>Res: {s['BU']} | Sup: {s['BE']}</div>", unsafe_allow_html=True)
                st.dataframe(s['Data'].tail())
    with c2:
        st.header(f"🔴 Bearish ({len(bears)})")
        for s in bears:
            with st.expander(f"{s['Sym']} (₹{s['Close']:.2f})"):
                st.markdown(f"<div class='scan-box bear-box'><b>MANDI</b><br>Res: {s['BU']} | Sup: {s['BE']}</div>", unsafe_allow_html=True)
                st.dataframe(s['Data'].tail())
