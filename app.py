import streamlit as st
import uuid
import os
from langchain_core.messages import HumanMessage, AIMessage
from src.agent.graph import build_invest_graph
from dotenv import load_dotenv

# 加载配置
load_dotenv()

# 初始化页面配置
st.set_page_config(page_title="Invest Agent 个人投研助手", page_icon="📈", layout="wide")

# 注入自定义 CSS 以实现高级排版和气泡样式
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Fira Sans', sans-serif !important;
}

code, [class*="st-"] code {
    font-family: 'Fira Code', monospace !important;
}

/* 聊天气泡背景优化 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background-color: rgba(245, 158, 11, 0.1) !important;
    border-left: 4px solid #F59E0B !important;
}
[data-testid="chatAvatarIcon-user"] {
    background-color: #F59E0B !important;
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    background-color: rgba(139, 92, 246, 0.1) !important;
    border-left: 4px solid #8B5CF6 !important;
}
[data-testid="chatAvatarIcon-assistant"] {
    background-color: #8B5CF6 !important;
}

/* 按钮交互动效优化 */
.stButton>button {
    transition: all 0.3s ease !important;
    border: 1px solid rgba(245, 158, 11, 0.5) !important;
}
.stButton>button:hover {
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.6) !important;
    transform: translateY(-2px) !important;
    border-color: #F59E0B !important;
    color: #F8FAFC !important;
}

/* 控制消息间距与标题缩放 */
[data-testid="stChatMessage"] {
    padding: 1.5rem !important;
    border-radius: 0.5rem !important;
}

[data-testid="stChatMessage"] h1 {
    font-size: 1.6rem !important;
    margin-bottom: 0.8rem !important;
}

[data-testid="stChatMessage"] h2 {
    font-size: 1.3rem !important;
    margin-bottom: 0.6rem !important;
}

[data-testid="stChatMessage"] h3 {
    font-size: 1.1rem !important;
    margin-bottom: 0.5rem !important;
}

[data-testid="stChatMessage"] h4 {
    font-size: 1.0rem !important;
    margin-bottom: 0.4rem !important;
}
</style>
""", unsafe_allow_html=True)

header_html = """
<div id="sticky-header-anchor"></div>
<style>
/* 利用 CSS :has 伪类将包含锚点的整个 Streamlit 容器变成粘贴定位 (Sticky) */
div[data-testid="stVerticalBlock"] > div:has(#sticky-header-anchor) {
    position: sticky;
    top: 2.8rem;
    z-index: 999;
    background-color: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(10px);
    padding-top: 0.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(245, 158, 11, 0.3);
    margin-bottom: 1rem;
}
</style>
<h1 style="margin:0; font-size: 2.2rem; font-weight: 700; color: #F8FAFC;">📈个人投研分析助手</h1>
<p style="margin: 0.5rem 0 0 0; color: #94A3B8; font-size: 1.1rem;">支持 <strong style="color:#F59E0B">A股 / 美股 / 国内期货</strong> 三市场深度投研，由 AI 首席分析师驱动。</p>
"""
st.markdown(header_html, unsafe_allow_html=True)

# 缓存并加载 LangGraph App
@st.cache_resource
def get_graph():
    return build_invest_graph()

app = get_graph()

# 初始化或者获取对历史对话的控制 (通过 session state)
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    
# 本地存储的用于 UI 展示的消息列表
if "messages" not in st.session_state:
    st.session_state.messages = []

# 将会话历史展示在网页中
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 提供一个侧边栏显示状态
with st.sidebar:
    st.header("⚙️ 状态信息")
    if os.environ.get("OPENAI_API_KEY"):
        st.success("API Key 已配置")
    else:
        st.error("未检测到 API Key，请检查 .env 配置")
        st.warning("在此状态下只能测试异常流。")
    
    st.divider()
    st.markdown("""**💡 使用说明**

支持以下三大市场：

🇨🇳 **A股**：直接输入名称或代码
> 如：宁德时代、002594

🇺🇸 **美股**：使用英文 Ticker 代码
> 如：AAPL苹果、NVDA英伟达

📦 **国内期货**：主力连续合约
> 如：螺纹钢RB888、豆粕M888
""")

    if st.button("清除对话重置状态"):
        st.session_state.messages = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()


# 接受用户输入
if prompt := st.chat_input("🇨🇳 A股：宁德时代  |  🇺🇸 美股：NVDA英伟达  |  📦 期货：螺纹钢RB888"):
    # 1. 把用户的输入添加到 UI 消息列表并立刻展示
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. 构建给 LangGraph 引擎的状态
    input_state = {
        "query": prompt,
        # 这里只需要传入最新的这句输入，因为 LangGraph 内部的 MemorySaver 会根据 thread_id 自动读取并使用历史消息
        "messages": [HumanMessage(content=prompt)]
    }
    
    # thread_id 配置必须传给 app
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    
    # 3. 产生 Assistant 的回复容器
    with st.chat_message("assistant"):
        # 用于展示节点执行进度的占位符
        status_placeholder = st.empty()
        status_placeholder.info("Agent 正在思考和规划分析逻辑...")
        
        final_report = ""
        error_msg = ""
        
        try:
            # 采用流式执行，方便捕捉每个节点的状态
            for output in app.stream(input_state, config=config):
                for key, value in output.items():
                    # 检查是否有错误传递出来
                    if "error" in value and value["error"]:
                        error_msg = value["error"]
                        status_placeholder.warning(f"节点 {key} 执行异常: {error_msg}")
                    else:
                        # 正常流转进度提示
                        if key == "intent_node":
                            assets = value.get("assets", [])
                            if assets:
                                names = [a.get("name", a.get("code", "未知")) for a in assets]
                                status_placeholder.info(f"成功识别分析目标: {', '.join(names)}... 准备获取数据")
                            else:
                                status_placeholder.warning("未识别出有效的股票/期货标准代码。")
                        elif key == "data_fetch_node":
                            status_placeholder.info("正在并向抓取市场行情和估值指标...")
                        elif key == "quantitative_node" or key == "fundamental_node":
                            status_placeholder.info(f"正在生成 {key} 的中间研判结果...")
                        elif key == "report_node":
                            status_placeholder.success("研报生成完毕！")
                            final_report = value.get("final_report", "")
        except Exception as e:
            st.error(f"图执行完全失败: {str(e)}")
            
        # 4. 拿到最终报告或错误信息后更新展示，并写入 session_state
        if final_report:
            import time
            def stream_data(text):
                """生成器：按块或按字符产生打字机效果"""
                # 为了看起来流畅，这里按块或少量字符 yield
                # 如果网速或生成速度快，甚至可以按字符：for char in text
                # 这里稍微大一点按字符块，或者也可以简单的按单个字
                for char in text:
                    yield char
                    time.sleep(0.005) # 极短的延迟，形成快速打字感
                    
            st.write_stream(stream_data(final_report))
            st.session_state.messages.append({"role": "assistant", "content": final_report})
        elif error_msg:
            # 如果 graph 返回的是带有 error_msg 且没有完整 report，补底渲染
            fallback_msg = f"**很抱歉，在执行过程中遇到错误中止：**\\n{error_msg}"
            st.markdown(fallback_msg)
            st.session_state.messages.append({"role": "assistant", "content": fallback_msg})
