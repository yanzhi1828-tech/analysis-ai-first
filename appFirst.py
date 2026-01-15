import streamlit as st
import yfinance as yf
from openai import OpenAI

# 1. 设置页面
st.set_page_config(page_title="Ryan's AI Analyst", page_icon="📈")

# 2. 读取 Key (从保险箱里拿)
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# 3. 核心功能：获取数据 (加了缓存魔法！让它记住数据，不用每次都去抓)
# ttl=3600 表示这份数据只保存 1 小时，1小时后会自动更新
@st.cache_data(ttl=3600)
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    return stock.info

st.title("Rayn's first try on building websites 🫶")
st.caption("Powered by GPT-4o & Streamlit Cloud")

# 输入框
ticker = st.text_input("输入股票代码 (如 NVDA):", "NVDA").upper()

if ticker:
    try:
        # 使用带缓存的函数来获取数据
        info = get_stock_data(ticker)
        
        # 显示数据
        st.header(info.get('longName', ticker))
        st.metric("最新股价", f"${info.get('currentPrice', 'N/A')}")
        
        summary = info.get('longBusinessSummary', 'No summary available.')
        
        # AI 分析按钮
        if st.button("让 AI 帮我分析"):
            with st.spinner('GPT-4o 正在思考...'):
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "用中文，给普通人而非专业投资人解释。"},
                        {"role": "user", "content": f"分析这家公司: {summary}"}
                    ]
                )
                st.markdown("### 🤖 分析报告")
                st.write(completion.choices[0].message.content)

    except Exception as e:
        # 即使报错了，也不要红一大片，显示得友好一点
        st.warning(f"⚠️ Yahoo 数据源暂时拥堵中 (Rate Limited)。\n建议：请等 1 分钟后再刷新网页，或者换个股票代码试试。")
        st.caption(f"错误详情: {e}")
