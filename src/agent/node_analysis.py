from .state import AgentState
import pandas as pd

import numpy as np

def calculate_macd(df, short=12, long=26, m=9):
    """计算 MACD 指标"""
    exp1 = df['收盘'].ewm(span=short, adjust=False).mean()
    exp2 = df['收盘'].ewm(span=long, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=m, adjust=False).mean()
    hist = (macd - signal) * 2
    return macd, signal, hist

def calculate_rsi(df, periods=14):
    """计算 RSI 指标"""
    delta = df['收盘'].diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.rolling(window=periods, min_periods=1).mean()
    avg_loss = loss.rolling(window=periods, min_periods=1).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_boll(df, window=20, num_std=2):
    """计算布林带 (BOLL)"""
    rolling_mean = df['收盘'].rolling(window=window).mean()
    rolling_std = df['收盘'].rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, rolling_mean, lower_band

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
            
            try:
                # 确保有足够的行数进行指标计算（至少60天）
                if len(df) < 60:
                   continue

                # 确保以日期排序，并转换为数值列
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.sort_values('日期').reset_index(drop=True)
                for col in ['收盘', '最高', '最低', '开盘', '成交量']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')

                # 1. 基础价格与涨跌幅
                latest_close = df.iloc[-1].get("收盘", 0)
                latest_date = df.iloc[-1].get("日期").strftime('%Y-%m-%d')
                oldest_close = df.iloc[0].get("收盘", 0)
                change_pct = ((latest_close - oldest_close) / oldest_close) * 100 if oldest_close else 0
                max_price = df["最高"].max() if "最高" in df.columns else 0
                min_price = df["最低"].min() if "最低" in df.columns else 0
                
                # 2. 计算均线系统 (MA5, MA10, MA20, MA60)
                df['MA5'] = df['收盘'].rolling(window=5).mean()
                df['MA10'] = df['收盘'].rolling(window=10).mean()
                df['MA20'] = df['收盘'].rolling(window=20).mean()
                df['MA60'] = df['收盘'].rolling(window=60).mean()
                
                ma5 = df['MA5'].iloc[-1]
                ma10 = df['MA10'].iloc[-1]
                ma20 = df['MA20'].iloc[-1]
                ma60 = df['MA60'].iloc[-1]
                
                ma_status = "多头排列(MA5>10>20)" if (ma5 > ma10 and ma10 > ma20) else "空头排列(MA5<10<20)" if (ma5 < ma10 and ma10 < ma20) else "震荡交织"
                
                # 3. 计算 MACD
                macd, signal, hist = calculate_macd(df)
                latest_macd = macd.iloc[-1]
                latest_signal = signal.iloc[-1]
                macd_status = "金叉(MACD>Signal)" if latest_macd > latest_signal else "死叉(MACD<Signal)"
                
                # 4. 计算 RSI (14)
                rsi = calculate_rsi(df)
                latest_rsi = rsi.iloc[-1]
                rsi_status = "超买(RSI>70)" if latest_rsi > 70 else "超卖(RSI<30)" if latest_rsi < 30 else "中性区间"
                
                # 5. 计算 BOLL 布林带
                upper, mid, lower = calculate_boll(df)
                latest_upper = upper.iloc[-1]
                latest_lower = lower.iloc[-1]
                pct_b = (latest_close - latest_lower) / (latest_upper - latest_lower) if (latest_upper - latest_lower) != 0 else 0.5
                boll_status = "中轨之上(强势)" if latest_close > mid.iloc[-1] else "中轨之下(弱势)"
                
                # 6. 量价分析 (近期成交量变化)
                vol_latest5 = df['成交量'].tail(5).mean()
                vol_prev5 = df['成交量'].shift(5).tail(5).mean()
                vol_status = "近期放量" if vol_latest5 > vol_prev5 * 1.2 else "近期缩量" if vol_latest5 < vol_prev5 * 0.8 else "量能平稳"

                # 拼装丰富版技术概览
                summary = f"【技术面详情（截至 {latest_date}，样本期近 {len(df)} 交易日，涨跌幅 {change_pct:.2f}%）】：\n"
                summary += f"1. 基础结构：最新收盘价 {latest_close:.2f}，历史高点 {max_price:.2f}，低点 {min_price:.2f}。\n"
                summary += f"2. 均线系统：MA5={ma5:.2f}, MA10={ma10:.2f}, MA20={ma20:.2f}, MA60={ma60:.2f}。当前均线呈现【{ma_status}】。\n"
                summary += f"3. 动能指标 (MACD)：MACD={latest_macd:.3f}, Signal={latest_signal:.3f}，当前处于【{macd_status}】状态。\n"
                summary += f"4. 相对强弱 (RSI14)：当前 RSI 值为 {latest_rsi:.2f}，位于【{rsi_status}】。\n"
                summary += f"5. 波动通道 (BOLL)：上轨={latest_upper:.2f}, 下轨={latest_lower:.2f}，股价处于【{boll_status}】，分位点：{pct_b:.1%}。\n"
                summary += f"6. 资金量能：5日均成交量对比前5日表现为【{vol_status}】。"
                
                existing_analysis = analysis_results.get(code, "")
                analysis_results[code] = existing_analysis + f"\n{summary}"
            except Exception as e:
                print(f"Error in detailed quant analysis for {code}: {e}")
                
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
