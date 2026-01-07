from typing import List, Dict, Tuple
from src.models import Trade, Position
from dataclasses import dataclass

@dataclass
class PnLRecord:
    symbol: str
    name: str
    side: str
    quantity: float
    price: float
    cost: float
    pnl: float
    trade_date: str
    industry: str

class PortfolioCalculator:
    def __init__(self, initial_positions: List[Position] = None):
        self.positions: Dict[str, Position] = {p.symbol: p for p in (initial_positions or [])}
        self.pnl_records: List[PnLRecord] = []

    def process_trades(self, trades: List[Trade], base_date=None):
        # 按时间排序
        # 处理 None 的日期
        for t in trades:
            if t.trade_date is None:
                t.trade_date = base_date or date.today()

        sorted_trades = sorted(trades, key=lambda x: (x.trade_date, x.trade_time or ""))
        
        for trade in sorted_trades:
            self._update_position(trade)

    def _update_position(self, trade: Trade):
        symbol = trade.symbol
        if trade.side == "BUY":
            if symbol not in self.positions:
                self.positions[symbol] = Position(
                    symbol=symbol,
                    name=trade.name,
                    quantity=trade.quantity,
                    avg_cost=trade.price,
                    industry=trade.industry
                )
            else:
                pos = self.positions[symbol]
                new_qty = pos.quantity + trade.quantity
                if new_qty > 0:
                    pos.avg_cost = (pos.quantity * pos.avg_cost + trade.quantity * trade.price) / new_qty
                pos.quantity = new_qty
        
        elif trade.side == "SELL":
            if symbol in self.positions:
                pos = self.positions[symbol]
                # 计算已实现盈亏
                # PnL = (卖出价 - 成本价) * 数量 * 乘数 - 手续费
                pnl = (trade.price - pos.avg_cost) * trade.quantity * trade.multiplier - trade.fee
                
                self.pnl_records.append(PnLRecord(
                    symbol=symbol,
                    name=pos.name,
                    side=trade.side,
                    quantity=trade.quantity,
                    price=trade.price,
                    cost=pos.avg_cost,
                    pnl=pnl,
                    trade_date=str(trade.trade_date),
                    industry=pos.industry
                ))
                
                pos.quantity -= trade.quantity
                # 如果清仓，可以选择保留或删除，这里保留但数量为0
                if pos.quantity <= 0:
                    pos.quantity = 0

    def get_snapshot(self) -> List[dict]:
        """返回当前持仓快照"""
        return [
            {
                "股票名称": p.name,
                "股票代码": p.symbol,
                "持仓量": p.quantity,
                "持仓均价": round(p.avg_cost, 3),
                "行业": p.industry,
                "占用金额": round(p.quantity * p.avg_cost, 2)
            }
            for p in self.positions.values() if p.quantity > 0
        ]

    def get_pnl_report(self) -> List[dict]:
        """返回已实现盈亏明细"""
        return [
            {
                "时间": r.trade_date,
                "代码": r.symbol,
                "名称": r.name,
                "方向": r.side,
                "数量": r.quantity,
                "成交均价": round(r.price, 3),
                "成本价": round(r.cost, 3),
                "产生的盈亏": round(r.pnl, 2),
                "行业": r.industry
            }
            for r in self.pnl_records
        ]

