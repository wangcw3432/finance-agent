from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .node_intent import parse_intent
from .node_fetch_data import fetch_data
from .node_analysis import analyze_quant, analyze_fundamental
from .node_report import generate_report

def build_invest_graph() -> StateGraph:
    """构建投研Agent的工作流图"""
    workflow = StateGraph(AgentState)
    
    # 意图分析节点已在 node_intent.py 中实现
    
    # 数据获取和分析节点均已引入


    # 添加节点
    workflow.add_node("intent_node", parse_intent)
    workflow.add_node("data_fetch_node", fetch_data)
    workflow.add_node("quantitative_node", analyze_quant)
    workflow.add_node("fundamental_node", analyze_fundamental)
    workflow.add_node("report_node", generate_report)
    
    # 定义边
    workflow.set_entry_point("intent_node")
    workflow.add_edge("intent_node", "data_fetch_node")
    workflow.add_edge("data_fetch_node", "quantitative_node")
    workflow.add_edge("quantitative_node", "fundamental_node")
    workflow.add_edge("fundamental_node", "report_node")
    workflow.add_edge("report_node", END)
    
    # 引入 MemorySaver 支持多轮对话的状态记忆
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
