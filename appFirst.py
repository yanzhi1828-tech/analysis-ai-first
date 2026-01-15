import streamlit as st
import requests
import wikipedia # 新增：维基百科库
from openai import OpenAI

# 1. 页面基础设置
st.set_page_config(page_title="Real-Time Market Analyst", page_icon="🏛️")

# 2. 获取 API Keys
try:
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    fmp_api_key = st.secrets["FMP_API_KEY"]
except:
    st.error("❌ Key 没配置好！请检查 Streamlit Secrets。")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# ---------------------------------------------------------
# 数据源 A: FMP API (只负责提供精准的数字)
# ---------------------------------------------------------
@st.cache_data(ttl=10) # 股价变动快，缓存10秒
def get_stock_price(symbol):
    # 使用 /quote 接口，这是 FMP 最基础且开放的接口
    url = f"https://financialmodelingprep.com/api/v3/quote/{symbol}?apikey={fmp_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if not data or (isinstance(data, dict) and 'Error Message' in data):
            return None
        return data[0] # 返回由交易所提供的原始数据
    except:
        return None

# ---------------------------------------------------------
# 数据源 B: Wikipedia (只负责提供客观的公司背景)
# ---------------------------------------------------------
@st.cache_data(ttl=86400) # 公司介绍一天变一次就够了
def get_wiki_info(query):
    try:
        # 搜索维基百科
        results = wikipedia.search(query)
        if not results:
            return None
        # 获取第一条结果的摘要（Summary）
        summary = wikipedia.summary(results[0], sentences=5) # 只取前5句精华
        return summary
    except:
        return None

# ---------------------------------------------------------
# 网页界面 UI
# ---------------------------------------------------------
st.title("🏛️ Institutional Grade Market Scanner")
st.caption("Data Sources: Financial Modeling Prep (Price) + Wikipedia (Context) | AI: GPT-4o (Analysis)")

ticker = st.text_input("Input Ticker (e.g., NVDA, BABA):", "NVDA").upper()

if ticker:
    # 1. 并行获取两个权威信源的数据
    with st.spinner('正在连接交易所和维基百科数据库...'):
        stock_data = get_stock_price(ticker)
        
        # 为了搜得准，我们用 "Ticker + Stock" 去搜维基，比如 "NVDA stock"
        # 但通常直接搜公司名更好，我们先用 API 拿到的公司名去搜
        company_name = stock_data.get('name') if stock_data else ticker
        wiki_text = get_wiki_info(company_name)

    if stock_data:
        # === 显示硬数据 (Hard Data) ===
        # 这些数据直接来自 API，没有任何 AI 加工，保证 100% 准确
        col1, col2 = st.columns(2)
        with col1:
            st.header(stock_data.get('name'))
            st.caption(f"Exchange: {stock_data.get('exchange')}")
        with col2:
            price = stock_data.get('price')
            change = stock_data.get('change')
            p_change = stock_data.get('changesPercentage')
            st.metric("Real-Time Price", f"${price}", f"{change} ({p_change}%)")
        
        # 显示维基百科原文 (增加可信度)
        if wiki_text:
            with st.expander("📖 查看维基百科原始词条 (Source of Truth)"):
                st.info(wiki_text)
        
        st.divider()

        # === AI 分析 (基于以上事实进行翻译) ===
        if st.button("Generate Insight Report"):
            with st.spinner('GPT-4o is synthesizing data...'):
                try:
                    # 这里的 Prompt 非常关键：我们强制 AI "Based on the text provided"
                    prompt = f"""
                    Role: You are a financial translator for high school students.
                    Task: Explain the company status using ONLY the provided data. Do NOT make up numbers.
                    
                    【Source 1: Financial Data】
                    - Company: {company_name}
                    - Current Price: ${price}
                    - Change: {p_change}%
                    
                    【Source 2: Wikipedia Summary】
                    - Context: {wiki_text}
                    
                    Output Requirements (Chinese):
                    1. 🏢 **Business Model**: Based on the Wikipedia text, strictly explain what they sell.
                    2. 📉 **Market Sentiment**: Based on the price change ({p_change}%), are people buying or selling today? Why?
                    3. ⚠️ **Risk Check**: Mention one general risk for this type of company.
                    4. 💡 **TL;DR**: A one-sentence summary.
                    """

                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a rigorous analyst. You rely on facts."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    st.markdown("### 🤖 Smart Analysis")
                    st.write(completion.choices[0].message.content)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")
    else:
        st.error("⚠️ Ticker Not Found. Please check if the ticker is valid (e.g., AAPL).")
