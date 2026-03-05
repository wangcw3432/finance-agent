import akshare as ak
import pandas as pd
import time
import os
import ssl
import urllib3
import requests
from typing import Dict, Any

# 禁用 requests 对这些域名的代理，防止由于系统代理导致的 HTTPSConnectionPool 错误
os.environ["NO_PROXY"] = "eastmoney.com,sina.com.cn,xueqiu.com,127.0.0.1,localhost"

# 禁用 SSL 警告并全局绕过证书验证，以解决 Sina Finance 返回的证书过期/无效错误
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# 对 akshare 底层使用的 requests 库全局禁用 SSL 验证
old_request = requests.Session.request
def new_request(*args, **kwargs):
    kwargs['verify'] = False
    return old_request(*args, **kwargs)
requests.Session.request = new_request

def get_stock_daily_hq(symbol: str, days: int = 365, max_retries: int = 3) -> pd.DataFrame:
    """获取A股历史行情数据(日频)，默认获取最近一年的数据"""
    from datetime import datetime, timedelta
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    
    # 尝试 1：东方财富日线接口
    for attempt in range(max_retries):
        try:
            stock_zh_a_hist_df = ak.stock_zh_a_hist(
                symbol=symbol, 
                period="daily", 
                start_date=start_date, 
                end_date=end_date, 
                adjust="qfq"
            )
            if not stock_zh_a_hist_df.empty:
               return stock_zh_a_hist_df
        except Exception as e:
            time.sleep(1) # wait before retrying
            
    # 尝试 2：如果东方财富日线多次失败 (可能被封IP或代理问题)，尝试使用新浪A股历史数据备用接口
    print(f"Eastmoney daily HQ failed for {symbol}. Trying Sina fallback...")
    try:
        # 新浪接口需要 sh/sz 前缀
        prefix = "sz"
        if symbol.startswith("6"):
            prefix = "sh"
        elif symbol.startswith("8") or symbol.startswith("4"):
            prefix = "bj"
            
        full_symbol = f"{prefix}{symbol}"
        
        # 新浪返回的数据列名和东财不同，为了下游处理兼容，我们需要重命名
        sina_df = ak.stock_zh_a_daily(symbol=full_symbol, start_date=start_date, end_date=end_date, adjust="qfq")
        if not sina_df.empty:
            sina_df = sina_df.rename(columns={
                "date": "日期",
                "open": "开盘",
                "high": "最高",
                "low": "最低",
                "close": "收盘",
                "volume": "成交量"
            })
            return sina_df
    except Exception as e:
        print(f"Error fetching daily hq for stock {symbol} (Sina Fallback): {e}")

    return pd.DataFrame()

def get_future_daily_hq(symbol: str, max_retries: int = 3) -> pd.DataFrame:
    """获取国内期货历史行情数据(日频)
    symbol 示例: 'RB0' (螺纹钢连续), 'M0' (豆粕连续) 或者具体的合约如 'rb2405'
    """
    for attempt in range(max_retries):
        try:
            # 新浪期货历史数据接口
            futures_df = ak.futures_zh_daily_sina(symbol=symbol)
            # 取最近的一年数据 (大约250个交易日)
            if not futures_df.empty:
                return futures_df.tail(250)
            return futures_df
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error fetching daily hq for future {symbol}: {e}")
                return pd.DataFrame()
            time.sleep(1)

def get_stock_fundamental(symbol: str, max_retries: int = 3) -> dict:
    """获取股票的基本面估值指标(如 PE, PB 等)"""
    prefix = "SZ"
    if symbol.startswith("6"):
        prefix = "SH"
    elif symbol.startswith("8") or symbol.startswith("4"):
        prefix = "BJ"
        
    full_symbol = f"{prefix}{symbol}"
    
    for attempt in range(max_retries):
        try:
            # 雪球单个股票行情及指标接口
            indicator_df = ak.stock_individual_spot_xq(symbol=full_symbol)
            if not indicator_df.empty:
                # 转换为字典形式便于读取
                return dict(zip(indicator_df['item'], indicator_df['value']))
            return {}
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Error fetching fundamental for stock {symbol}: {e}")
                return {}
            time.sleep(1)
