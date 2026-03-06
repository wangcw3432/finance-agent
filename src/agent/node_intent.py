from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import os
from .state import AgentState

def init_llm():
    """初始化豆包大模型客户端"""
    # 这些变量需要配置在系统环境变量中，或者通过 dotenv 加载
    return ChatOpenAI(
        model=os.environ.get("LLM_MODEL_NAME", "ep-xxxxx"),
        openai_api_base=os.environ.get("OPENAI_API_BASE", "https://ark.cn-beijing.volces.com/api/v3"),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        temperature=0.1
    )

def parse_intent(state: AgentState) -> AgentState:
    """第一步：意图解析节点，从用户输入中提取关注的资产和分析维度"""
    llm = init_llm()
    
    system_prompt = """
你是一个专业的金融分析助手。你的任务是从用户的最新查询中提取出他们想要分析的资产（A股、美股、期货）以及他们关注的分析维度（基本面、技术面、消息面等）。
请务必结合之前的“对话历史”上下文来理解指代词（如“它”、“这只股票”是指向之前讨论过的哪一只股票）。

请严格以 JSON 格式输出，参考以下 Schema:
{
    "assets": [
        {"type": "stock", "code": "股票代码", "name": "名称"},
        {"type": "stock_us", "code": "美股代码", "name": "名称"},
        {"type": "future", "code": "期货代码", "name": "名称"}
    ],
    "intents": ["基本面", "技术面", "相关新闻"]
}
注意：
1. 如果涉及A股，type为`stock`，code 请猜测6位代码（如 300750）。
2. 如果涉及美股（如苹果、英伟达、特斯拉等），type为`stock_us`，code 必须直接使用纯英文字母大写的Ticker代码（例如 AAPL、NVDA、TSLA）。
3. 如果涉及国内期货，type为`future`，code 填写常见的主力合约代码（如 rb888, m888等）。
"""
    
    # 提取最近的对话历史 (不包含最后一条，最后一条是当前 user 输入)
    history_messages = state.get("messages", [])[:-1] if state.get("messages") else []
    
    messages = [SystemMessage(content=system_prompt)] + history_messages + [
        HumanMessage(content=f"当前用户的最新查询是：{state.get('query', '')}。请结合历史对话给出提取的 JSON。")
    ]
    
    try:
        response = llm.invoke(messages)
        content = response.content
        
        # 尝试清理可能存在的 markdown json 标记
        if "```json" in content:
            content = content.replace("```json", "").replace("```", "").strip()
            
        parsed_intent = json.loads(content)
        
        # 更新状态
        return {"assets": parsed_intent.get("assets", []), "intents": parsed_intent.get("intents", [])}
    except Exception as e:
        print(f"Failed to parse intent: {e}")
        return {"error": f"意图解析失败: {str(e)}"}
