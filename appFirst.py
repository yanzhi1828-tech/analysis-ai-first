import streamlit as st
import requests
from openai import OpenAI

# 1. 页面基础设置
st.set_page_config(page_title="Gen Z Market Scanner", page_icon="⚡️")

# 2. 从保险箱获取两把钥匙
openai_api_key = st.secrets["OPENAI_API_KEY"]
fmp_api_key = st.secrets["FMP_API_KEY"]

# 初始化 OpenAI
client = OpenAI(api_key=openai_api_key)

# ---------------------------------------------------------
# 核心函数：改用 FMP API 获取数据 (稳定！不封号！)
# ---------------------------------------------------------
@st.cache_data(ttl=3600) # 依然加上缓存，省着点用免费额度
def get_company_data(symbol):
    # 这是 FMP 的官方接口，专门查公司简介和价格
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={fmp_api_key}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # 如果返回空列表，说明股票代码输错了
        if not data:
            return None
            
        # FMP 返回的是一个列表，我们取第一个
        return data[0]
    except Exception as e:
        st.error(f"API 连接失败: {e}")
        return None

# ---------------------------------------------------------
# 网页界面 UI
# ---------------------------------------------------------
st.title("⚡️ Gen Z Market Scanner")
st.caption("No buffering. Real-time API data. Powered by FMP & GPT-4o.")

# 输入框
ticker = st.text_input("输入股票代码 (Ticker):", "AAPL").upper()

if ticker:
    # 显示加载状态
    with st.spinner(f'正在通过高速 API 拉取 {ticker} 数据...'):
        
        # 调用我们新写的函数
        info = get_company_data(ticker)
        
        if info is None:
            st.error("⚠️ 找不到这个公司，请检查代码是否正确（如: NVDA, TSLA）")
        else:
            # === 展示数据 (数据字段变了，我们需要对应 FMP 的格式) ===
            
            # 第一行：大标题和价格
            col1, col2 = st.columns([2, 1])
            with col1:
                st.header(info.get('companyName', ticker))
                st.write(f"🏢 交易所: {info.get('exchangeShortName')}")
            with col2:
                # 价格信息
                price = info.get('price')
                currency = info.get('currency')
                st.metric("当前价格", f"{price} {currency}")

            # 公司简介 (Description)
            description = info.get('description', '暂无简介')
            
            # 行业标签
            st.info(f"🏷️ 行业: {info.get('industry')} | 👨‍💼 CEO: {info.get('ceo')}")

            st.divider()

            # === AI 分析部分 ===
            if st.button("🔮 激活 GPT-4o 深度分析"):
                with st.spinner('AI 正在阅读分析师报告...'):
                    try:
                        prompt = f"""
                        Target Audience: Gen Z students.
                        Task: Analyze this company based on the description.
                        Tone: Fun, Insightful, No jargon.
                        Language: Chinese (中文).
                        
                        Company: {info.get('companyName')}
                        Description: {description}
                        Price: {price}
                        
                        Questions to answer:
                        1. 💰 它是靠什么赚大钱的？(Business Model)
                        2. 🚀 为什么它最近这么受关注？(Based on general knowledge + description)
                        3. ⚠️ 投资它的最大风险是什么？
                        """

                        completion = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are a financial influencer."},
                                {"role": "user", "content": prompt}
                            ]
                        )
                        st.markdown("### 🤖 深度分析")
                        st.write(completion.choices[0].message.content)
                        
                    except Exception as e:
                        st.error(f"AI 思考超时: {e}")

# 底部版权
st.markdown("---")
st.caption("Data Source: Financial Modeling Prep API | Analysis: OpenAI GPT-4o")
