from typing import TypedDict, Annotated, List, Dict, Any
import operator
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AssetInfo(TypedDict):
    """资产信息"""
    type: str  # "stock" | "future"
    code: str  # 资产代码,如 "300750"
    name: str  # 资产名称,如 "宁德时代"

class AgentState(TypedDict):
    """分析Agent的状态"""
    # 消息历史，使用 add_messages 聚合器支持追加
    messages: Annotated[list[BaseMessage], add_messages]
    
    # 当前用户的最新查询语句
    query: str
    
    # 解析出的需要分析的资产列表
    assets: List[AssetInfo]
    
    # 意图和关注点，比如 ['基本面', '技术面']
    intents: List[str]
    
    # 市场行情和技术面数据 (按资产代码存储)
    market_data: Dict[str, Any]
    
    # 基本面数据 (按资产代码存储)
    fundamental_data: Dict[str, Any]
    
    # 各个维度的分析结果
    analysis_results: Dict[str, str]
    
    # 最终汇总的报告
    final_report: str
    
    # 运行时的错误信息
    error: str
