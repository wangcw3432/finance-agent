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
        
    system_prompt = f"""你是一位宏观投资研究体系中的首席分析师 (Chief Analyst)。
你需要协调手下的6大研究小组（内资股票组、外资股票组、大宗商品组、加密货币组、中国宏观组、美国宏观组），根据以下提供的数据事实，对用户的初始需求进行极致深度的解答。
用户的初始需求是：“{query}”

下属研究小组提供的深度数据事实如下：
{context}

要求：
1. 必须完全模仿多小组协作的专业风格，输出极度规范的《首席分析师综合研报》。
2. 你输出的全部内容必须采用原生的、标准的 Markdown 语法（如 `#`, `##`, `-`, `**`, `> ` 等），不要使用任何特殊的 unicode 框线（如 ━━━）。请确保在任何 Markdown 渲染器下都呈现完美的排版。
3. 研报需严格包含以下层级结构，并尽可能丰富细节：
   
# 📊 首席分析师综合研报

## 一、 核心结论与综合判断
高度精炼地总结核心倾向（强烈看多/看多/中性震荡/看空/强烈看空），并给出明确的投资定调和核心驱动逻辑。

## 二、 深度分组研究发现
（请根据上下文数据，智能分配到对应的研究小组名下。以下为重点必须覆盖的分析维度：）

### 1. [基本面/宏观小组] 核心基本面与信息面深度剖析
- **估值水位**：结合提供的市盈率(PE(TTM))、市净率(PB)、总市值等估值数据，深度评价当前估值的历史分位点和安全边际。
- **行业地位**：剖析行业的相对高低估状态。
- **信息面映射**：如果有财报、新闻、政策等基本面事件数据，请深度剖析其对资产价值的长期影响。

### 2. [量化/技术分析小组] 技术面与量价结构分析
- **趋势与均线系统**：解读MA5/10/20/60的排列状态（多头/空头/纠缠），判断短期与中期趋势的坚固程度。
- **动能与震荡指标**：深度剖析MACD（金叉/死叉/背离）和 RSI(14) 的超买超卖状态，判断当前的上涨/下跌动能及爆发潜力。
- **布林带通道**：分析价格在BOLL轨道(%b分位点)的位置及通道缩放、开口朝向等迹象。
- **资金博弈（量价配合）**：精确解读近期成交量的变化趋势（缩量/放量），判断主力资金入场或离场痕迹，以及量价背离信号。

## 三、 具体交易策略与执行建议
要求极其细致、具有实操性的建议（这部分最为关键），请以列表或表格形式呈现：
- **核心操作评级**：（如：分批建仓 / 底仓持有 / 逢高减磅 / 清仓观望）
- **入场与出场区间（关键点位参考）**：
  - **强支撑区（防守止损线）**：(给出具备技术依据的明确数字指引)
  - **第一阻力位 / 目标获利区**：(给出明确数字和涨幅预期)
- **仓位管理建议**：初始建仓比例(如轻仓试探、半仓介入等)与后续加仓/减仓节奏。
- **操作周期**：这笔交易适用的周期（超短线/波段/中长线持有）。
   
## 四、 核心风险提示与证伪条件
详细列举可能导致上述看多/看空判断完全失效的“黑天鹅”因素、估值陷阱下行风险或关键跌破点（破某点即逻辑证伪）。

4. 语气必须极其客观严谨、层级分明，展现出统帅全局且关注实操的研究深度。所有具体的数值（指标值、市值、PE等）必须且只能基于上述提供的数据事实推演。如果提供的数据不足以得出某个维度的结论，请诚实说明“当前数据不足以支撑详细判断”。
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
