from .state import AgentState
from .node_intent import init_llm
from langchain_core.messages import SystemMessage, HumanMessage

def generate_report(state: AgentState) -> AgentState:
    """第五步：研报生成节点"""
    llm = init_llm()
    
    query = state.get("query", "")
    assets = state.get("assets", [])
    analysis_results = state.get("analysis_results", {})
    error = state.get("error", "")
    
    if error:
        return {"final_report": f"执行过程中出现错误: {error}"}
        
    if not assets:
        return {"final_report": "未能识别出需要分析的资产。请提供具体的股票名称、代码或期货品种。"}
        
    # 构建给大模型的 Prompt 上下文
    context = ""
    for asset in assets:
        code = asset.get("code")
        name = asset.get("name")
        res = analysis_results.get(code, "无可用分析数据。")
        context += f"\\n--- 资产：{name} ({code}) ---\\n{res}\\n"
        
    system_prompt = f"""你是一位资深的券商投研分析师。
请根据以下提供的数据事实（包含技术面或基本面等），回答用户的初始问题。
用户的初始问题是：“{query}”

分析数据如下：
{context}

要求：
1. 以专业的Markdown格式输出研报。
2. 包含“投资摘要”、“详细分析(技术面/基本面)”、“风险提示”等常规研报结构。
3. 语气客观严谨，禁止过度夸大收益。所有结论需基于提供的数据。
"""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content="请帮我生成一份专业的投研报告。")
    ]
    
    try:
        response = llm.invoke(messages)
        return {"final_report": response.content}
    except Exception as e:
        return {"error": f"报告生成失败: {str(e)}"}
