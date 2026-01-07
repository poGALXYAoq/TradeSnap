import pandas as pd
import io
import json
from datetime import datetime, date
from typing import List, Dict, Optional
from src.models import Trade
import os

# 期货合约乘数映射
FUTURES_MULTIPLIER = {
    'IF': 300,
    'IH': 300,
    'IC': 200,
    'IM': 200,
}

class IndustryLookup:
    def __init__(self, cn_path: str, hk_path: str):
        self.lookup: Dict[str, str] = {}
        self._load_cn(cn_path)
        self._load_hk(hk_path)

    def _load_cn(self, path: str):
        if os.path.exists(path):
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                code = str(row['证券代码'])
                # 只取一级行业
                industry = str(row['所属申万行业名称(2021)']).split('--')[0]
                self.lookup[code] = industry

    def _load_hk(self, path: str):
        if os.path.exists(path):
            df = pd.read_csv(path)
            for _, row in df.iterrows():
                code = str(row['证券代码'])
                # 港股代码补齐 5 位数字
                if code.isdigit():
                    code = code.zfill(5) + ".HK"
                # 只取一级行业
                industry = str(row['所属申万行业名称(港股)(2021)']).split('--')[0]
                self.lookup[code] = industry

    def get_industry(self, code: str) -> str:
        # 尝试完全匹配
        if code in self.lookup:
            return self.lookup[code]
        # 尝试去掉后缀
        base_code = code.split('.')[0]
        if base_code in self.lookup:
            return self.lookup[base_code]
        # 针对港股，如果是 5 位数字，补全后缀再试
        if base_code.isdigit() and len(base_code) <= 5:
            hk_code = base_code.zfill(5) + ".HK"
            if hk_code in self.lookup:
                return self.lookup[hk_code]
        return "未知"

# 初始化行业查找
industry_lookup = IndustryLookup(
    'industry/industry_CN.csv',
    'industry/industry_HK.csv'
)

def normalize_ashare_code(code: str) -> str:
    """补全 A 股代码后缀"""
    code = str(code).strip().zfill(6)
    if code.startswith(('60', '68', '90')):
        return f"{code}.SH"
    elif code.startswith(('00', '30', '20')):
        return f"{code}.SZ"
    elif code.startswith(('43', '83', '87', '88')):
        return f"{code}.BJ"
    return code

def clean_numeric(value) -> float:
    """清理数字字符串，处理千分位逗号等"""
    if pd.isna(value) or value == '':
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    # 移除逗号并转换为 float
    s = str(value).replace(',', '').strip()
    try:
        return float(s)
    except ValueError:
        return 0.0

def parse_ashare_csv(file_content: str) -> List[Trade]:
    """解析 A 股 CSV"""
    df = pd.read_csv(io.StringIO(file_content))
    trades = []
    
    for _, row in df.iterrows():
        # 日期处理
        trade_date_str = str(row.get('成交日期', '')).strip()
        if not trade_date_str or trade_date_str == 'nan':
            # 后续会由外部传入的基准日期填充，这里先占位
            trade_date = None
        else:
            try:
                trade_date = pd.to_datetime(trade_date_str).date()
            except:
                trade_date = None
        
        # 证券代码规范化
        raw_code = str(row['证券代码'])
        symbol = normalize_ashare_code(raw_code)
        
        # 方向映射
        side = "BUY" if row['操作'] == '买入' else "SELL"
        
        trades.append(Trade(
            symbol=symbol,
            name=str(row['证券名称']),
            side=side,
            price=clean_numeric(row['成交均价']),
            quantity=clean_numeric(row['成交数量']),
            trade_date=trade_date,
            fee=clean_numeric(row.get('手续费', 0.0)),
            industry=industry_lookup.get_industry(symbol)
        ))
    return trades

def parse_futures_csv(file_content: str) -> List[Trade]:
    """解析中国期货 CSV"""
    df = pd.read_csv(io.StringIO(file_content))
    trades = []
    
    for _, row in df.iterrows():
        symbol = str(row['合约']).strip()
        # 提取品种代码 (如 IF2606 -> IF)
        product_code = ''.join([c for c in symbol if c.isalpha()])
        multiplier = FUTURES_MULTIPLIER.get(product_code, 1.0)
        
        # 方向判断
        side_raw = str(row['买卖']).strip()
        side = "BUY" if "买" in side_raw else "SELL"
        
        trades.append(Trade(
            symbol=symbol,
            name=symbol,
            side=side,
            price=clean_numeric(row['成交均价']),
            quantity=clean_numeric(row['成交手数']),
            trade_date=None, # 期货 CSV 通常没有日期列
            fee=clean_numeric(row.get('手续费', 0.0)),
            multiplier=multiplier,
            industry="期货"
        ))
    return trades

def parse_ai_json(json_str: str) -> List[Trade]:
    """解析 Ollama 返回的 JSON 字符串"""
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            return []
        
        trades = []
        for item in data:
            symbol = str(item.get('code', ''))
            # 港股代码补全
            if symbol.isdigit() and len(symbol) <= 5:
                symbol = symbol.zfill(5) + ".HK"
            
            trades.append(Trade(
                symbol=symbol,
                name=item.get('name', symbol),
                side=item.get('side', 'BUY'),
                price=clean_numeric(item.get('price', 0)),
                quantity=clean_numeric(item.get('qty', 0)),
                trade_date=None,
                fee=clean_numeric(item.get('fee', 0)),
                industry=industry_lookup.get_industry(symbol)
            ))
        return trades
    except:
        return []
