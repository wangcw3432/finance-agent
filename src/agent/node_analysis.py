from .state import AgentState
import pandas as pd

def analyze_quant(state: AgentState) -> AgentState:
    """第三步：技术面/量化分析节点"""
    intents = state.get("intents", [])
    if "技术面" not in intents and "量化" not in intents and not intents:
        # 如果用户明确不需要技术面分析，可以跳过（暂略简化，如果 intents 为空则全分析）
        pass
        
    market_data = state.get("market_data", {})
    analysis_results = state.get("analysis_results", {})
    
    for code, data in market_data.items():
        if isinstance(data, dict) and "error" in data:
            continue
            
        if isinstance(data, list) and len(data) > 0:
            # 转换为 DataFrame 方便计算
            df = pd.DataFrame(data)
            
            # 这里简单算个涨跌幅和均价，作为技术面总结给后续 LLM 用
            try:
                # 假设 AKShare 返回列包含 收盘, 最高, 最低等
                latest_close = df.iloc[-1].get("收盘", 0)
                oldest_close = df.iloc[0].get("收盘", 0)
                
                change_pct = ((latest_close - oldest_close) / oldest_close) * 100 if oldest_close else 0
                max_price = df["最高"].max() if "最高" in df.columns else 0
                min_price = df["最低"].min() if "最低" in df.columns else 0
                
                summary = f"最近60个交易日，标的区间涨跌幅约 {change_pct:.2f}%。最高价 {max_price}，最低价 {min_price}。最新收盘价 {latest_close}。"
                
                existing_analysis = analysis_results.get(code, "")
                analysis_results[code] = existing_analysis + f"\\n【技术面概览】：{summary}"
            except Exception as e:
                print(f"Error in quant analysis for {code}: {e}")
                
    return {"analysis_results": analysis_results}

def analyze_fundamental(state: AgentState) -> AgentState:
    """第四步：基本面分析节点"""
    intents = state.get("intents", [])
    if "基本面" not in intents and not intents:
        pass
        
    analysis_results = state.get("analysis_results", {})
    fundamental_data = state.get("fundamental_data", {})
    assets = state.get("assets", [])
    
    for asset in assets:
        code = asset.get("code")
        atype = asset.get("type")
        
        if atype == "stock":
            existing_analysis = analysis_results.get(code, "")
            fund_info = fundamental_data.get(code, {})
            
            if "error" in fund_info or not fund_info:
                analysis_results[code] = existing_analysis + f"\\n【基本面概览】：暂无有效的最新估值数据。"
            else:
                date = fund_info.get("时间", "最新交易日")
                pe_ttm = fund_info.get("市盈率(TTM)", fund_info.get("市盈率(动)", "未知"))
                pb = fund_info.get("市净率", "未知")
                total_mv = fund_info.get("资产净值/总市值", "未知")
                
                analysis_results[code] = existing_analysis + f"\\n【基本面概览 (截至 {date})】：总市值(元)为 {total_mv}，市盈率(TTM)为 {pe_ttm}，市净率(PB)为 {pb}。可结合行业平均估值做进一步判断。"
            
    return {"analysis_results": analysis_results}
