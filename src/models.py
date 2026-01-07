from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional

@dataclass
class Trade:
    symbol: str          # 证券代码 (e.g., 000400.SZ, IF2606)
    name: str            # 证券名称
    side: str            # 交易方向: "BUY" or "SELL"
    price: float         # 成交价格
    quantity: float      # 成交数量 (手数或股数)
    trade_date: date     # 成交日期
    trade_time: Optional[time] = None  # 成交时间
    fee: float = 0.0     # 手续费
    multiplier: float = 1.0  # 乘数 (期货使用)
    industry: str = ""    # 行业分类

@dataclass
class Position:
    symbol: str          # 证券代码
    name: str            # 证券名称
    quantity: float      # 当前持仓量
    avg_cost: float      # 持仓均价 (成本)
    industry: str = ""    # 行业分类
    market_price: float = 0.0  # 最新收盘价 (预留)

    @property
    def total_cost(self) -> float:
        return self.quantity * self.avg_cost

