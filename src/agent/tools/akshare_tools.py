import akshare as ak
import pandas as pd
from typing import Dict, Any

def get_stock_daily_hq(symbol: str, days: int = 365) -> pd.DataFrame:
    """获取A股历史行情数据(日频)，默认获取最近一年的数据"""
    try:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # 东方财富 A 股历史行情，symbol 传入 6 位代码（如 300750）
        # adjust="qfq" 为前复权，更适合技术面分析
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=symbol, 
            period="daily", 
            start_date=start_date, 
            end_date=end_date, 
            adjust="qfq"
        )
        return stock_zh_a_hist_df
    except Exception as e:
        print(f"Error fetching daily hq for stock {symbol}: {e}")
        return pd.DataFrame()

def get_future_daily_hq(symbol: str) -> pd.DataFrame:
    """获取国内期货历史行情数据(日频)
    symbol 示例: 'RB0' (螺纹钢连续), 'M0' (豆粕连续) 或者具体的合约如 'rb2405'
    """
    try:
        # 新浪期货历史数据接口
        futures_df = ak.futures_zh_daily_sina(symbol=symbol)
        # 取最近的一年数据 (大约250个交易日)
        if not futures_df.empty:
            return futures_df.tail(250)
        return futures_df
    except Exception as e:
        print(f"Error fetching daily hq for future {symbol}: {e}")
        return pd.DataFrame()

def get_stock_fundamental(symbol: str) -> dict:
    """获取股票的基本面估值指标(如 PE, PB 等)"""
    try:
        # 判断股票市场前缀
        prefix = "SZ"
        if symbol.startswith("6"):
            prefix = "SH"
        elif symbol.startswith("8") or symbol.startswith("4"):
            prefix = "BJ"
            
        full_symbol = f"{prefix}{symbol}"
        
        # 雪球单个股票行情及指标接口
        indicator_df = ak.stock_individual_spot_xq(symbol=full_symbol)
        if not indicator_df.empty:
            # 转换为字典形式便于读取
            return dict(zip(indicator_df['item'], indicator_df['value']))
        return {}
    except Exception as e:
        print(f"Error fetching fundamental for stock {symbol}: {e}")
        return {}
