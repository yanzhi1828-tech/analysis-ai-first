import streamlit as st
import yfinance as yf
from openai import OpenAI

# 1. 填入你的 Key
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# 2. 连接 AI
client = OpenAI(api_key=OPENAI_API_KEY)

# 3. 网页内容
st.title("Rayn's first try on building websites🫶")

ticker = st.text_input("输入股票代码 (如 NVDA):", "NVDA").upper()

if ticker:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        st.header(info.get('longName', ticker))
        st.metric("股价", f"${info.get('currentPrice', 'N/A')}")
        
        summary = info.get('longBusinessSummary', 'No summary.')
        
        if st.button("开始分析"):
            with st.spinner('AI 正在思考...'):
                completion = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "用中文，给普通人们而非专业的投资人解释。"},
                        {"role": "user", "content": f"分析这家公司: {summary}"}
                    ]
                )
                st.write(completion.choices[0].message.content)

    except Exception as e:
        st.error(f"出错了: {e}")
