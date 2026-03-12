import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import io
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="प्रो ट्रेडिंग टर्मिनल", layout="wide", page_icon="📈")

# --- ऐप की मेमोरी (Session State) ---
if 'app_mode' not in st.session_state:
    st.session_state.app_mode = "📊 एडवांस एनालाइज़र (All-in-One)"
if 'target_ticker' not in st.session_state:
    st.session_state.target_ticker = None

# --- जादुई कॉलबैक फंक्शन (पेज बदलने के लिए) ---
def switch_to_analyzer(ticker_symbol):
    st.session_state.target_ticker = ticker_symbol
    st.session_state.app_mode = "📊 एडवांस एनालाइज़र (All-in-One)"

# ---------------------------------------------------------
# 1. डेटाबेस लोडर
# ---------------------------------------------------------
@st.cache_data 
def get_all_stocks():
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            csv_data = response.read().decode('utf-8')
            df = pd.read_csv(io.StringIO(csv_data))
            stock_dict = {}
            for index, row in df.iterrows():
                name = str(row['NAME OF COMPANY'])
                raw_symbol = str(row['SYMBOL'])
                stock_dict[f"{name} ({raw_symbol})"] = raw_symbol
            return stock_dict
    except Exception as e:
        return {"Reliance Industries (RELIANCE)": "RELIANCE", "Tata Motors (TATAMOTORS)": "TATAMOTORS", "State Bank of India (SBIN)": "SBIN"}

indian_stocks = get_all_stocks()

nifty_50_list = {
    "Reliance": "RELIANCE", "TCS": "TCS", "HDFC Bank": "HDFCBANK", "ICICI Bank": "ICICIBANK", 
    "Bharti Airtel": "BHARTIARTL", "SBI": "SBIN", "Infosys": "INFY", "L&T": "LT", 
    "ITC": "ITC", "Bajaj Finance": "BAJFINANCE", "Axis Bank": "AXISBANK", "Kotak Bank": "KOTAKBANK", 
    "Tata Motors": "TATAMOTORS", "M&M": "M&M", "Maruti Suzuki": "MARUTI", "Sun Pharma": "SUNPHARMA", 
    "HCL Tech": "HCLTECH", "Asian Paints": "ASIANPAINT", "NTPC": "NTPC", "Tata Steel": "TATASTEEL", 
    "Titan": "TITAN", "UltraTech": "ULTRACEMCO", "Bajaj Finserv": "BAJAJFINSV", "Nestle": "NESTLEIND", 
    "Power Grid": "POWERGRID", "Adani Ent": "ADANIENT", "JSW Steel": "JSWSTEEL", "Grasim": "GRASIM", 
    "Tata Consumer": "TATACONSUM", "HUL": "HINDUNILVR", "ONGC": "ONGC", "Coal India": "COALINDIA", 
    "Cipla": "CIPLA", "HDFC Life": "HDFCLIFE", "Dr Reddy": "DRREDDY", "Apollo Hosp": "APOLLOHOSP", 
    "Britannia": "BRITANNIA", "Eicher Motors": "EICHERMOT", "Bajaj Auto": "BAJAJ-AUTO", "Divis Labs": "DIVISLAB", 
    "Tech Mahindra": "TECHM", "Wipro": "WIPRO", "IndusInd Bank": "INDUSINDBK", "Shriram Fin": "SHRIRAMFIN", 
    "LTIMindtree": "LTIM", "Hero MotoCorp": "HEROMOTOCO", "SBI Life": "SBILIFE", "BPCL": "BPCL", 
    "Adani Ports": "ADANIPORTS", "Hindalco": "HINDALCO"
}

# ---------------------------------------------------------
# 2. एडवांस टेक्निकल इंडिकेटर्स
# ---------------------------------------------------------
def calculate_indicators(data):
    data['SMA_20'] = data['Close'].rolling(window=20).mean()
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).ewm(alpha=1/14, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))
    data['Vol_SMA'] = data['Volume'].rolling(window=20).mean()
    
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['MACD_Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    
    data['BB_std'] = data['Close'].rolling(window=20).std()
    data['BB_upper'] = data['SMA_20'] + (data['BB_std'] * 2)
    data['BB_lower'] = data['SMA_20'] - (data['BB_std'] * 2)
    return data

# ---------------------------------------------------------
# 3. साइडबार
# ---------------------------------------------------------
st.sidebar.title("⚙️ सिस्टम मेन्यू")
app_mode = st.sidebar.radio("मोड चुनें:", ["📊 एडवांस एनालाइज़र (All-in-One)", "🔍 सुपर स्कैनर (AI Scanner)"], key="app_mode")

# =========================================================
# मोड 1: एडवांस एनालाइज़र (सब कुछ एक जगह)
# =========================================================
if st.session_state.app_mode == "📊 एडवांस एनालाइज़र (All-in-One)":
    st.title("📈 अल्टीमेट शेयर मार्केट एनालाइज़र (V7.0)")
    
    exchange = st.radio("एक्सचेंज:", ["NSE (.NS)", "BSE (.BO)"], horizontal=True)
    
    stock_list = list(indian_stocks.keys())
    default_idx = 0
    if st.session_state.target_ticker:
        for i, s in enumerate(stock_list):
            if f"({st.session_state.target_ticker})" in s:
                default_idx = i
                break
        st.session_state.target_ticker = None # काम होने के बाद मेमोरी साफ़ करना
        
    selected_company = st.selectbox("शेयर चुनें या सर्च करें:", stock_list, index=default_idx)
    ticker = indian_stocks[selected_company] + (".NS" if "NSE" in exchange else ".BO")

    if st.button("स्मार्ट 360° एनालिसिस करें"):
        with st.spinner(f"🚀 {selected_company} का डेटा डिकोड किया जा रहा है..."):
            try:
                stock = yf.Ticker(ticker)
                data = stock.history(period="1y")
                info = stock.info
                
                if data.empty:
                    st.error("❌ डेटा नहीं मिला।")
                else:
                    data = calculate_indicators(data)
                    last_close = data['Close'].iloc[-1]
                    
                    high_52 = info.get('fiftyTwoWeekHigh', 'N/A')
                    low_52 = info.get('fiftyTwoWeekLow', 'N/A')
                    pe_ratio = info.get('trailingPE', 'N/A')
                    market_cap = info.get('marketCap', 'N/A')
                    analyst_count = info.get('numberOfAnalystOpinions', 'N/A')
                    target_price = info.get('targetMeanPrice', 'N/A')
                    
                    pe_status = "N/A"
                    if pe_ratio != 'N/A' and pe_ratio is not None:
                        try:
                            pe_val = float(pe_ratio)
                            if pe_val < 20: pe_status = "🟢 सस्ता (Undervalued)"
                            elif pe_val < 50: pe_status = "🟡 नॉर्मल (Fair Valuation)"
                            else: pe_status = "🔴 काफी महंगा (Overvalued)"
                        except:
                            pass

                    st.markdown("### 🏢 1. कंपनी की स्थिति (Fundamentals)")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("अभी का भाव", f"₹{last_close:.2f}")
                    col2.metric("52 हफ्ते का हाई", f"₹{high_52}")
                    col3.metric("52 हफ्ते का लो", f"₹{low_52}")
                    col4.metric("P/E Ratio", f"{pe_ratio}")
                    mc_display = f"₹ {market_cap / 10000000:.2f} Cr" if market_cap != 'N/A' else 'N/A'
                    col5.metric("मार्केट कैप", f"{mc_display}")
                    
                    st.info(f"💡 **वैल्यूएशन चेक:** P/E Ratio के हिसाब से यह शेयर अभी **{pe_status}** है।")

                    rec_key = info.get('recommendationKey', 'hold').lower()
                    if 'strong_buy' in rec_key: meter_val = 100; color = "#00b300"; text = "STRONG BUY (बहुत मज़बूत)"
                    elif 'buy' in rec_key: meter_val = 75; color = "#00cc66"; text = "BUY (खरीदें)"
                    elif 'hold' in rec_key: meter_val = 50; color = "#ffcc00"; text = "HOLD (न्यूट्रल/बनाए रखें)"
                    elif 'sell' in rec_key and 'strong' not in rec_key: meter_val = 25; color = "#ff6666"; text = "SELL (बेचें)"
                    elif 'strong_sell' in rec_key: meter_val = 10; color = "#cc0000"; text = "STRONG SELL (भारी गिरावट)"
                    else: meter_val = 50; color = "#ffcc00"; text = "HOLD (डेटा नहीं)"

                    st.markdown("### 🎛️ 2. एक्सपर्ट सेंटीमेंट मीटर (Rating)")
                    st.write(f"बाज़ार के **{analyst_count} बड़े ब्रोकरेज हाउस** की राय | **एक्सपर्ट्स का टारगेट: ₹{target_price}**")
                    st.markdown(f'''
                        <div style="width: 100%; background-color: #e6e6e6; border-radius: 10px; height: 30px; margin-bottom: 20px;">
                            <div style="width: {meter_val}%; background-color: {color}; height: 100%; border-radius: 10px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; transition: width 1s;">
                                {meter_val}% ({text})
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)

                    prev_high = data['High'].iloc[-2]
                    prev_low = data['Low'].iloc[-2]
                    prev_close = data['Close'].iloc[-2]
                    pivot = (prev_high + prev_low + prev_close) / 3
                    target_1 = (2 * pivot) - prev_low
                    stop_loss = (2 * pivot) - prev_high

                    st.markdown("### 🎯 3. ऑटोमैटिक ट्रेड लेवल (पिवट पॉइंट्स)")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("एंट्री (अभी का भाव)", f"₹{last_close:.2f}")
                    c2.metric("🟢 टारगेट (मुनाफा बुक करें)", f"₹{target_1:.2f}")
                    c3.metric("🔴 स्टॉप-लॉस (घाटा काटें)", f"₹{stop_loss:.2f}")

                    last_rsi = data['RSI'].iloc[-1]
                    last_macd = data['MACD'].iloc[-1]
                    last_signal = data['MACD_Signal'].iloc[-1]
                    last_vol = data['Volume'].iloc[-1]
                    vol_sma = data['Vol_SMA'].iloc[-1]

                    st.markdown("### 🧠 4. मास्टरमाइंड AI डिसीजन (Triple Confirmation)")
                    col_pro, col_con = st.columns(2)
                    pros, cons = [], []
                    
                    if data['SMA_20'].iloc[-1] > data['SMA_50'].iloc[-1]: pros.append("📈 **ट्रेंड:** शेयर मज़बूत अपट्रेंड में है।")
                    else: cons.append("📉 **ट्रेंड:** शेयर डाउनट्रेंड में है।")
                    
                    if last_rsi < 40: pros.append(f"🔋 **RSI ({last_rsi:.0f}):** शेयर सस्ता (Oversold) है।")
                    elif last_rsi > 70: cons.append(f"⚠️ **RSI ({last_rsi:.0f}):** शेयर बहुत महंगा (Overbought) है।")
                    
                    if last_macd > last_signal: pros.append("🔥 **MACD:** बुलिश क्रॉसओवर (खरीददारों की ताकत बढ़ रही है)।")
                    else: cons.append("❄️ **MACD:** बियरिश (बिकवाली का दबाव है)।")
                    
                    if last_vol > (vol_sma * 1.5): pros.append(f"💥 **वॉल्यूम:** भारी खरीदारी हो रही है।")
                    
                    if 'buy' in rec_key: pros.append(f"👔 **एक्सपर्ट्स:** एनालिस्ट्स खरीदने की सलाह दे रहे हैं।")
                    elif 'sell' in rec_key: cons.append(f"👔 **एक्सपर्ट्स:** एनालिस्ट्स बेचने की सलाह दे रहे हैं।")
                    
                    with col_pro:
                        st.success("✅ **मज़बूती (Pros)**")
                        for p in pros: st.write("- " + p)
                    with col_con:
                        st.error("❌ **कमज़ोरी (Cons)**")
                        for c in cons: st.write("- " + c)

                    st.markdown("### 📊 5. टेक्निकल चार्ट्स")
                    st.line_chart(data[['Close', 'SMA_20', 'SMA_50']])
                    st.caption("नीचे MACD का मोमेंटम चार्ट है:")
                    st.area_chart(data[['MACD', 'MACD_Signal']].tail(60))

            except Exception as e:
                st.error(f"❌ तकनीकी खराबी: {e}")

# =========================================================
# मोड 2: सुपर स्कैनर (Dual Option + Callback Auto-Link)
# =========================================================
elif st.session_state.app_mode == "🔍 सुपर स्कैनर (AI Scanner)":
    st.title("🤖 प्रो AI ऑटो-स्कैनर")
    
    scan_type = st.radio("आप किन शेयरों को स्कैन करना चाहते हैं?", ["🏆 निफ्टी 50 (Top 50)", "🌊 पूरा बाज़ार (All NSE)"], horizontal=True)
    st.write("बाज़ार के टॉप शेयरों में **'Triple Confirmation' (MACD + Trend + RSI)** वाली स्ट्रेटेजी लगाकर परफेक्ट शेयर ढूंढें!")

    if scan_type == "🏆 निफ्टी 50 (Top 50)":
        stocks_to_scan = list(nifty_50_list.items())
        st.info("💡 **निफ्टी 50:** इसमें भारत की 50 सबसे बड़ी और सुरक्षित कंपनियाँ स्कैन की जाएंगी।")
        button_text = "🚀 निफ्टी 50 स्कैन शुरू करें"
        total_count = len(stocks_to_scan)
    else:
        scan_limit = st.slider("पूरे बाज़ार में से कितने शेयरों को स्कैन करना है?", min_value=50, max_value=2000, value=100, step=50)
        stocks_to_scan = list(indian_stocks.items())[:scan_limit]
        st.warning(f"⏳ **ध्यान दें:** {scan_limit} शेयरों का डेटा इंटरनेट से डाउनलोड होने में कुछ समय लग सकता है।")
        button_text = f"🚀 अभी {scan_limit} शेयर स्कैन करें"
        total_count = scan_limit

    if st.button(button_text):
        progress_bar = st.progress(0)
        results = []
        
        for i, (name, raw_ticker) in enumerate(stocks_to_scan):
            try:
                ticker = raw_ticker + ".NS"
                stock = yf.Ticker(ticker)
                data = stock.history(period="3mo")
                
                if not data.empty and len(data) > 30: 
                    data = calculate_indicators(data)
                    last_close = data['Close'].iloc[-1]
                    last_rsi = data['RSI'].iloc[-1]
                    last_macd = data['MACD'].iloc[-1]
                    last_signal = data['MACD_Signal'].iloc[-1]
                    
                    if (last_close > data['SMA_50'].iloc[-1]) and (50 <= last_rsi <= 70) and (last_macd > last_signal):
                        results.append({
                            "name": name, 
                            "ticker": raw_ticker,
                            "price": last_close, 
                            "rsi": last_rsi
                        })
            except:
                pass
            
            progress_bar.progress((i + 1) / total_count)
        
        st.success(f"✅ स्कैनिंग पूरी हो गई! ({total_count} शेयरों में से {len(results)} मास्टरपीस मिले)")
        
        if len(results) > 0:
            st.write("### 🎯 आज के 'Triple Confirmation' वाले कड़क शेयर:")
            
            # --- नया और फिक्स्ड कॉलबैक बटन ---
            for res in results:
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                    col1.markdown(f"**{res['name']}**")
                    col2.markdown(f"₹{res['price']:.2f}")
                    col3.markdown(f"**RSI:** {res['rsi']:.1f}")
                    
                    # यह बटन सीधा 'switch_to_analyzer' फंक्शन को कॉल करेगा
                    col4.button("🔍 एनालाइज़ करें", key=f"btn_{res['ticker']}", on_click=switch_to_analyzer, args=(res['ticker'],))
                    st.markdown("---")
        else:
            st.warning("⚠️ आज के मार्केट में इस कड़क स्ट्रेटेजी पर कोई भी शेयर खरा नहीं उतरा।")