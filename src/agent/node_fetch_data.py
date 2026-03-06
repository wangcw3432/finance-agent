from .state import AgentState
from .tools.akshare_tools import get_stock_daily_hq, get_future_daily_hq, get_stock_fundamental, get_us_stock_daily_hq

def fetch_data(state: AgentState) -> AgentState:
    """第二步：数据获取节点"""
    assets = state.get("assets", [])
    market_data = state.get("market_data", {})
    
    fundamental_data = state.get("fundamental_data", {})
    
    for asset in assets:
        code = asset.get("code")
        atype = asset.get("type")
        
        if not code:
            continue
            
        if atype == "stock":
            # 简单示例：直接拉取该股票这几年的日线数据 (使用前复权)
            df = get_stock_daily_hq(code)
            if not df.empty:
                # 存入 state. 实际业务中可能只存最近 N 天的数据以防超出 LLM Context
                market_data[code] = df.tail(60).to_dict('records') # 取最近60个交易日
            else:
                market_data[code] = {"error": "Failed to fetch stock data"}
                
            # 获取股票的基本面估值
            fund_data = get_stock_fundamental(code)
            if fund_data:
                fundamental_data[code] = fund_data
            else:
                fundamental_data[code] = {"error": "Failed to fetch fundamental data"}

        elif atype == "stock_us":
            # 拉取美股日线数据
            us_df = get_us_stock_daily_hq(code)
            if not us_df.empty:
                market_data[code] = us_df.tail(60).to_dict('records')
            else:
                market_data[code] = {"error": "Failed to fetch US stock data"}
            
            # 美股基本面暂不通过该接口获取，留空或给提示
            fundamental_data[code] = {"error": "US stock fundamental data not available via current api"}

        elif atype == "future":
            # 拉取期货日线数据
            fut_df = get_future_daily_hq(code)
            if not fut_df.empty:
                # 存入 state, 截取最近 60 个交易日
                market_data[code] = fut_df.tail(60).to_dict('records')
            else:
                market_data[code] = {"error": "Failed to fetch future data"}
            
    return {"market_data": market_data, "fundamental_data": fundamental_data}
