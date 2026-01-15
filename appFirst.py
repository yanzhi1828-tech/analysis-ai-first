import streamlit as st
import requests
from openai import OpenAI

# ================= 1. 网站全局配置 (这是变身"大网站"的关键) =================
st.set_page_config(
    page_title="AlphaStream Pro", 
    page_icon="🚀",
    layout="wide",  # <--- 关键！开启宽屏模式，利用整个屏幕空间
    initial_sidebar_state="expanded" # 默认打开侧边栏
)

# 加载 CSS 美化 (让界面更现代化)
st.markdown("""
<style>
    .metric-card {
        background-color: #0e1117;
        border: 1px solid #30333d;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. 初始化 API =================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    twelve_api_key = st.secrets["TWELVE_DATA_KEY"]
except:
    st.error("❌ 请先配置 Secrets！")
    st.stop()

# ================= 3. 功能函数：智能搜索与数据 =================

# 🔍 搜索功能：把 "Apple" 变成 "AAPL"
def search_symbol(query):
    # Twelve Data 的搜索接口
    url = f"https://api.twelvedata.com/symbol_search?symbol={query}&apikey={twelve_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        # 返回搜索结果列表 (如果出错返回空)
        if 'data' in data:
            return data['data'] # 这是一个包含多个匹配公司的列表
        return []
    except:
        return []

# 📊 获取实时数据
def get_stock_data(symbol):
    url = f"https://api.twelvedata.com/quote?symbol={symbol}&apikey={twelve_api_key}"
    try:
        response = requests.get(url)
        data = response.json()
        if 'price' in data:
            return data
        return None
    except:
        return None

# ================= 4. UI 布局：侧边栏 (Sidebar) =================

with st.sidebar:
    st.title("🔍 市场导航")
    st.caption("Search by Name or Ticker")
    
    # --- 搜索模式切换 ---
    search_mode = st.radio("选择搜索方式:", ["公司名称搜索 (Name)", "股票代码 (Ticker)"])
    
    selected_symbol = None
    
    if search_mode == "公司名称搜索 (Name)":
        # 1. 用户输入名字
        query = st.text_input("输入公司名 (例如: Apple, Tesla)", "")
        
        if query:
            # 2. 调用 API 搜索
            results = search_symbol(query)
            
            if results:
                # 3. 让用户从下拉菜单里选一个 (可能搜出好几个)
                # 格式化选项为: "Apple Inc (AAPL) - NASDAQ"
                options = {f"{item['instrument_name']} ({item['symbol']}) - {item['exchange']}": item['symbol'] for item in results}
                
                choice = st.selectbox("找到以下匹配:", list(options.keys()))
                selected_symbol = options[choice] # 拿到对应的 AAPL
            else:
                st.warning("未找到匹配公司，请尝试英文名称。")
    
    else:
        # 直接输入代码模式
        raw_ticker = st.text_input("输入代码 (例如: NVDA)", "NVDA").upper()
        selected_symbol = raw_ticker

    st.markdown("---")
    st.info("💡 提示: 输入英文公司名准确率更高。\nAPI provided by Twelve Data.")

# ================= 5. 主界面 (Main Area) =================

st.title("🚀 AlphaStream Pro Dashboard")

if selected_symbol:
    # 获取数据
    with st.spinner(f'正在从华尔街拉取 {selected_symbol} 的数据...'):
        data = get_stock_data(selected_symbol)

    if data:
        # --- 第一部分：顶部核心指标 (类似于彭博终端) ---
        # 使用 4 列布局
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("公司名称", data.get('name', selected_symbol))
        with col2:
            st.metric("最新价格", f"${data['price']}")
        with col3:
            # 自动判断颜色
            change = float(data['change'])
            st.metric("涨跌额", f"{change:.2f}", delta=change)
        with col4:
            pct = float(data['percent_change'])
            st.metric("涨跌幅", f"{pct:.2f}%", delta=f"{pct}%")
            
        st.divider()

        # --- 第二部分：使用 Tab 分页 (显得内容很丰富) ---
        tab1, tab2 = st.tabs(["🔮 AI 深度分析", "📊 原始数据"])

        with tab1:
            st.subheader("GPT-4o 投资分析报告")
            if st.button("生成分析报告 (Click to Generate)"):
                with st.spinner('AI 正在阅读财报并分析市场情绪...'):
                    try:
                        prompt = f"""
                        Role: Hedge Fund Analyst.
                        Target: High School / College Students.
                        Task: Analyze {data.get('name')} ({selected_symbol}).
                        Data: Price ${data['price']}, Change {data['percent_change']}%.
                        
                        Answer in Chinese:
                        1. **What do they do?** (Business Model in simple terms)
                        2. **Why is the stock moving today?** (Speculate based on price change)
                        3. **Bull Case vs Bear Case** (Good scenario vs Bad scenario)
                        4. **Final Verdict**: Rating (1-10).
                        """
                        res = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.write(res.choices[0].message.content)
                    except Exception as e:
                        st.error(str(e))
            else:
                st.info("点击按钮开始分析 (节省 API 额度)")

        with tab2:
            st.subheader("交易所原始数据")
            st.json(data)
            
    else:
        # 如果 Twelve Data 没找到 (或者是免费版额度限制)
        st.error(f"无法获取 {selected_symbol} 的数据。")
        st.caption("原因可能是：1. 输入了错误的名称/代码 2. Twelve Data 免费版每分钟只有 8 次请求限制 (歇一会再试)。")

else:
    st.info("👈 请在左侧侧边栏输入公司名称或代码开始。")
