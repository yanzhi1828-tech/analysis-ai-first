import streamlit as st
import yfinance as yf
import wikipedia
from openai import OpenAI
import time

# ================= 1. 基础配置 =================
st.set_page_config(page_title="Market Insights Pro", page_icon="📈")

# 检查 OpenAI Key
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
except:
    st.error("❌ 请先在 Streamlit Secrets 里配置 OPENAI_API_KEY")
    st.stop()

# ================= 2. 核心数据函数 (防弹版) =================

# 🏆 获取价格：使用 Yahoo Finance，但加上强力缓存
@st.cache_data(ttl=600)  # 600秒(10分钟)内如果不换股票，就不重新请求 Yahoo
def get_yahoo_data(symbol):
    try:
        # 使用 yfinance 获取对象
        stock = yf.Ticker(symbol)
        
        # 获取 fast_info (比 .info 更快，封锁概率更低)
        price = stock.fast_info['last_price']
        prev_close = stock.fast_info['previous_close']
        
        # 计算涨跌幅
        change = price - prev_close
        pct_change = (change / prev_close) * 100
        
        # 尝试获取公司全名 (如果失败就用代码代替)
        try:
            name = stock.info.get('longName', symbol)
            exchange = stock.info.get('exchange', 'US Market')
        except:
            name = symbol
            exchange = "N/A"

        return {
            "price": price,
            "change": change,
            "pct_change": pct_change,
            "name": name,
            "exchange": exchange
        }
    except Exception as e:
        print(f"Yahoo Error: {e}") # 在后台打印错误
        return None

# 📚 获取背景：使用 Wikipedia (非常稳定)
@st.cache_data(ttl=3600*24) # 介绍数据缓存 24 小时
def get_wiki_summary(query):
    try:
        # 搜索并获取摘要
        results = wikipedia.search(f"{query} company")
        if not results:
            return None
        # 获取第一条结果
        summary = wikipedia.summary(results[0], sentences=4)
        return summary
    except:
        return None

# ================= 3. 网页界面 UI =================

st.title("📈 Institutional Market Scanner")
st.caption("Live Data: Yahoo Finance | Context: Wikipedia | Analysis: GPT-4o")

# 输入框
ticker = st.text_input("输入股票代码 (Ticker):", "NVDA").upper()

if ticker:
    # 1. 获取数据 (并行处理)
    with st.spinner('正在从 Yahoo 和 Wikipedia 调取数据...'):
        yahoo_data = get_yahoo_data(ticker)
        
        # 用 Yahoo 的公司名去搜 Wiki，如果 Yahoo 挂了就用 Ticker 搜
        search_term = yahoo_data['name'] if yahoo_data else ticker
        wiki_text = get_wiki_summary(search_term)

    # 2. 展示数据模块
    
    # --- 模块 A: 实时价格 (Yahoo) ---
    if yahoo_data:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.header(yahoo_data['name'])
            st.caption(f"交易所: {yahoo_data['exchange']}")
        with col2:
            st.metric(
                "实时股价 (Real-time)", 
                f"${yahoo_data['price']:.2f}", 
                f"{yahoo_data['change']:.2f} ({yahoo_data['pct_change']:.2f}%)"
            )
    else:
        # 即使 Yahoo 挂了，也不要红屏报错，显示一个优雅的提示
        st.warning(f"⚠️ 暂时无法连接 Yahoo Finance 获取 {ticker} 的实时股价。")
        st.caption("原因：可能是 Yahoo 对云服务器进行了临时限流 (Rate Limit)。请过几分钟再试。")
        # 设定一个假数据让 AI 依然能跑 (Optional)
        yahoo_data = {"name": ticker, "price": "N/A", "pct_change": "N/A"}

    st.divider()

    # --- 模块 B: 公司背景 (Wikipedia) ---
    if wiki_text:
        st.subheader("📖 维基百科摘要 (Wikipedia)")
        st.info(wiki_text)
    else:
        st.warning("未找到维基百科相关词条。")

    # --- 模块 C: AI 分析 (GPT-4o) ---
    # 只要有 Wiki 或者 Yahoo 任意一个数据，AI 就可以工作！
    if st.button("🔮 生成 AI 投资分析报告"):
        if not wiki_text and not yahoo_data:
            st.error("数据不足，AI 无法分析。")
        else:
            with st.spinner('GPT-4o 正在阅读所有数据并撰写报告...'):
                try:
                    prompt = f"""
                    Role: Financial Analyst for Gen Z.
                    Task: Analyze {ticker} based strictly on the provided data.
                    
                    【Data Source 1: Market Data】
                    - Name: {yahoo_data.get('name')}
                    - Price: {yahoo_data.get('price')}
                    - Trend: {yahoo_data.get('pct_change')}
                    
                    【Data Source 2: Context】
                    - Wikipedia Summary: {wiki_text}
                    
                    Please answer in Chinese (中文):
                    1. 🏢 **Business Model**: What do they actually sell? (Explain simply)
                    2. 🎢 **Current Vibe**: Based on the wiki and price, is it a hot stock?
                    3. ⚠️ **Main Risks**: What could go wrong?
                    4. 💡 **Verdict**: One sentence summary.
                    """
                    
                    completion = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a helpful financial assistant."},
                            {"role": "user", "content": prompt}
                        ]
                    )
                    st.markdown("### 🤖 深度分析")
                    st.write(completion.choices[0].message.content)
                    
                except Exception as e:
                    st.error(f"AI Error: {e}")

# 底部
st.markdown("---")
st.markdown("Data reliability provided by **Yahoo Finance** & **Wikipedia**")
