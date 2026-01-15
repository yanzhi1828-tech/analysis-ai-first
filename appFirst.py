import streamlit as st
import requests

st.title("🕵️‍♂️ API 侦探模式")

# 1. 直接把 Key 打印出来检查 (只显示前5位，安全起见)
# 这样你可以确认 Streamlit 到底有没有读到你的 Key
try:
    fmp_api_key = st.secrets["FMP_API_KEY"]
    st.write(f"🔑 当前使用的 Key (前5位): **{fmp_api_key[:5]}...**")
except Exception as e:
    st.error("❌ 致命错误: Secrets 里根本没找到 FMP_API_KEY！请去 Settings -> Secrets 检查。")
    st.stop()

# 2. 手动测试
symbol = st.text_input("输入代码", "AAPL")

if st.button("测试连接"):
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={fmp_api_key}"
    
    st.write(f"正在连接: `{url}` (Key已隐藏)")
    
    try:
        response = requests.get(url)
        data = response.json()
        
        # === 真相时刻：直接显示 API 回复了什么 ===
        st.subheader("🔍 FMP 回复的原始数据:")
        st.json(data) 
        
        # 帮你看一眼到底是啥问题
        if isinstance(data, dict) and "Error Message" in data:
            st.error(f"找到原因了！FMP 说: {data['Error Message']}")
        elif isinstance(data, list) and len(data) > 0:
            st.success("连接成功！数据是正常的列表。")
        else:
            st.warning("数据是空的，或者格式很奇怪。")

    except Exception as e:
        st.error(f"代码崩了: {e}")
