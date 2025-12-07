import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta

# -------------------------------------------------
# 1) Your F&O stock list (static, no Dhan)
# -------------------------------------------------

FO_STOCKS = [
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

# -------------------------------------------------
# 2) Fetch OHLC data from Yahoo (High & Low only)
# -------------------------------------------------

@st.cache_data(show_spinner=True)
def fetch_yahoo_ohlc(symbol: str, start: date, end: date) -> pd.DataFrame:
    """
    Fetch daily OHLC data from Yahoo Finance for an NSE stock.
    symbol: NSE symbol without suffix (e.g., 'KOTAKBANK').
    Uses .NS suffix for Yahoo.
    """
    ticker = symbol.upper().strip() + ".NS"
    data = yf.download(ticker, start=start, end=end + timedelta(days=1))

    if data.empty:
        return pd.DataFrame()

    data = data.reset_index()
    # Ensure we always have Date, High, Low
    data.rename(columns={"Date": "Date", "High": "High", "Low": "Low"}, inplace=True)
    return data[["Date", "High", "Low"]]


# -------------------------------------------------
# 3) VNS Logic using only High & Low (robust)
# -------------------------------------------------

def compute_vns_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply VNS Teji/Mandi/Atak/Reaction/Breakout/Breakdown logic
    based ONLY on High & Low.

    Input df must have columns: Date, High, Low (daily data).

    Returns:
        DataFrame with columns ['Date', 'Price', 'Type', 'Info']
    """

    # --- Defensive cleaning of input df ---
    if df is None or df.empty:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    df = df.copy()

    # 1) Ensure Date column exists and is datetime
    if "Date" not in df.columns:
        if df.index.name == "Date":
            df = df.reset_index()
        else:
            # If this happens, something is off with upstream data
            raise ValueError("Input df has no 'Date' column for VNS logic.")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])
    if df.empty:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    # 2) Ensure High/Low are numeric
    df["High"] = pd.to_numeric(df["High"], errors="coerce")
    df["Low"] = pd.to_numeric(df["Low"], errors="coerce")
    df = df.dropna(subset=["High", "Low"])
    if df.empty or len(df) < 2:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    # 3) Sort df by date
    df = df.sort_values("Date").reset_index(drop=True)

    # --- VNS core state ---
    last_teji_high = None   # last Teji (BU) pivot high
    last_mandi_low = None   # last Mandi (BE) pivot low

    signals = []

    # 1st pass: Teji / Mandi / Atak / Reaction
    for i in range(1, len(df)):
        y = df.iloc[i - 1]
        t = df.iloc[i]

        y_high = float(y["High"])
        y_low = float(y["Low"])
        t_high = float(t["High"])
        t_low = float(t["Low"])

        # A) Today's low breaks yesterday's low → yesterday's high = pivot high
        if t_low < y_low:
            pivot_price = y_high
            pivot_date = y["Date"]

            if last_teji_high is None:
                signal_type = "Teji (BU)"
                info = "First Teji: low break after this high."
                last_teji_high = pivot_price
            else:
                if pivot_price > last_teji_high:
                    signal_type = "Teji (BU)"
                    info = "New higher Teji high."
                    last_teji_high = pivot_price
                elif pivot_price < last_teji_high:
                    signal_type = "Atak (Double Top)"
                    info = f"Lower high vs previous Teji {last_teji_high:.2f}."
                else:
                    signal_type = "Reaction"
                    info = "Low break, but equal to previous Teji high."

            signals.append(
                {
                    "Date": pivot_date,
                    "Price": pivot_price,
                    "Type": signal_type,
                    "Info": info,
                }
            )

        # B) Today's high breaks yesterday's high → yesterday's low = pivot low
        if t_high > y_high:
            pivot_price = y_low
            pivot_date = y["Date"]

            if last_mandi_low is None:
                signal_type = "Mandi (BE)"
                info = "First Mandi: high break after this low."
                last_mandi_low = pivot_price
            else:
                if pivot_price < last_mandi_low:
                    signal_type = "Mandi (BE)"
                    info = "New lower Mandi low."
                    last_mandi_low = pivot_price
                elif pivot_price > last_mandi_low:
                    signal_type = "Atak (Double Bottom)"
                    info = f"Higher low vs previous Mandi {last_mandi_low:.2f}."
                else:
                    signal_type = "Reaction"
                    info = "High break, but equal to previous Mandi low."

            signals.append(
                {
                    "Date": pivot_date,
                    "Price": pivot_price,
                    "Type": signal_type,
                    "Info": info,
                }
            )

    # No signals? Return empty.
    if not signals:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    sig_df = pd.DataFrame(signals)

    # --- Defensive cleaning of sig_df before sorting ---
    if "Date" not in sig_df.columns:
        return pd.DataFrame(columns=["Date", "Price", "Type", "Info"])

    sig_df["Date"] = pd.to_datetime(sig_df["Date"], errors="coerce")
    sig_df = sig_df.dropna(subset=["Date"])
    if sig_df.empty:
        return sig_df

    # Sort by date
    sig_df = sig_df.sort_values("Date").reset_index(drop=True)

    # 2nd pass: Breakout / Breakdown (Teji–Mandi–Teji, Mandi–Teji–Mandi)
    extra_rows = []

    last_teji_idx = None
    last_mandi_idx = None

    for i, row in sig_df.iterrows():
        stype = str(row["Type"])

        if stype.startswith("Teji"):
            last_teji_idx = i
        if stype.startswith("Mandi"):
            last_mandi_idx = i

        # Need both to even consider breakout/breakdown
        if last_teji_idx is not None and last_mandi_idx is not None:
            teji_date = sig_df.loc[last_teji_idx, "Date"]
            mandi_date = sig_df.loc[last_mandi_idx, "Date"]

            # Case 1: Teji older, then Mandi newer → watch for breakout above Teji
            if teji_date < mandi_date:
                teji_price = sig_df.loc[last_teji_idx, "Price"]
                post = df[df["Date"] > mandi_date]
                crossed = post[post["High"] >= teji_price]
                if not crossed.empty:
                    brk_row = crossed.iloc[0]
                    extra_rows.append(
                        {
                            "Date": brk_row["Date"],
                            "Price": teji_price,
                            "Type": "Breakout",
                            "Info": f"Price High crossed Teji level {teji_price:.2f} after Mandi.",
                        }
                    )
                    # Reset so we don’t keep repeating on the same pair
                    last_teji_idx = None
                    last_mandi_idx = None

            # Case 2: Mandi older, then Teji newer → watch for breakdown below Mandi
            elif mandi_date < teji_date:
                mandi_price = sig_df.loc[last_mandi_idx, "Price"]
                post = df[df["Date"] > teji_date]
                crossed = post[post["Low"] <= mandi_price]
                if not crossed.empty:
                    brk_row = crossed.iloc[0]
                    extra_rows.append(
                        {
                            "Date": brk_row["Date"],
                            "Price": mandi_price,
                            "Type": "Breakdown",
                            "Info": f"Price Low broke Mandi level {mandi_price:.2f} after Teji.",
                        }
                    )
                    last_teji_idx = None
                    last_mandi_idx = None

    if extra_rows:
        extra_df = pd.DataFrame(extra_rows)
        extra_df["Date"] = pd.to_datetime(extra_df["Date"], errors="coerce")
        sig_df = pd.concat([sig_df, extra_df], ignore_index=True)
        sig_df = sig_df.dropna(subset=["Date"])
        sig_df = sig_df.sort_values("Date").reset_index(drop=True)

    return sig_df


# -------------------------------------------------
# 4) Streamlit UI
# -------------------------------------------------

st.set_page_config(page_title="VNS Theory Scanner (High/Low Only)", layout="wide")

st.title("📈 VNS Theory Scanner (High & Low Based)")
st.write(
    "Select an F&O stock, choose a duration, fetch data from Yahoo Finance, "
    "and apply VNS logic (Teji / Mandi / Atak / Breakout / Breakdown) using only High & Low."
)

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")

    st.subheader("1️⃣ Select F&O Stock")
    default_index = FO_STOCKS.index("KOTAKBANK") if "KOTAKBANK" in FO_STOCKS else 0
    selected_symbol = st.selectbox("F&O Stock Symbol", FO_STOCKS, index=default_index)

    st.subheader("2️⃣ Select Duration")
    today = date.today()

    duration_choice = st.radio(
        "Time Range",
        ["1 week", "1 month", "2 months", "3 months", "Custom"],
        index=1,
    )

    if duration_choice == "1 week":
        start_date = today - timedelta(days=7)
        end_date = today
    elif duration_choice == "1 month":
        start_date = today - timedelta(days=30)
        end_date = today
    elif duration_choice == "2 months":
        start_date = today - timedelta(days=60)
        end_date = today
    elif duration_choice == "3 months":
        start_date = today - timedelta(days=90)
        end_date = today
    else:
        # custom range
        custom_range = st.date_input(
            "Custom Date Range",
            value=(today - timedelta(days=90), today),
        )
        if isinstance(custom_range, (tuple, list)):
            start_date, end_date = custom_range
        else:
            # streamlit can give single date if user mis-clicks
            end_date = custom_range
            start_date = end_date - timedelta(days=60)

    st.markdown("---")
    run_button = st.button("🚀 Run VNS Scan")

# Main section
if run_button:
    st.subheader(f"📊 Yahoo Price Data: {selected_symbol} ({start_date} → {end_date})")

    data = fetch_yahoo_ohlc(selected_symbol, start=start_date, end=end_date)

    if data.empty:
        st.error(
            "No data returned from Yahoo Finance. "
            "Check symbol, date range, or internet/Yahoo connectivity."
        )
    else:
        st.write("Raw High/Low data used for VNS logic:")
        st.dataframe(data, use_container_width=True)

        st.subheader("🧠 VNS Signals (High/Low Only)")
        sig_df = compute_vns_signals(data)

        if sig_df.empty:
            st.warning("No VNS signals detected in the selected period.")
        else:
            st.dataframe(sig_df, use_container_width=True)
else:
    st.info("Select stock & duration in the sidebar, then click **Run VNS Scan**.")
