from dataclasses import dataclass
@dataclass
class Portfolio:
    cash: float = 10000.0
    qty: float = 0.0
    avg_price: float = 0.0
    def equity(self, last: float) -> float:
        return self.cash + self.qty * last
    def update_fill(self, side:str, qty:float, price:float, fee:float):
        if side=="buy":
            cost=qty*price+fee
            self.cash -= cost
            self.avg_price = (self.avg_price*self.qty + qty*price)/ (self.qty+qty) if self.qty+qty>0 else price
            self.qty += qty
        else:
            proceeds=qty*price - fee
            self.cash += proceeds
            self.qty -= qty
            if self.qty<=0: self.avg_price=0.0
