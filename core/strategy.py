class EmaCross:
    def __init__(self, fast:int=9, slow:int=21):
        self.fast=fast; self.slow=slow; self.buf=[]
    @staticmethod
    def _ema(vals, n):
        if not vals: return None
        k=2/(n+1); e=vals[0]
        for v in vals[1:]: e = v*k + e*(1-k)
        return e
    def push(self, price:float):
        self.buf.append(price)
        lim=max(self.fast,self.slow)+2
        if len(self.buf)>lim: self.buf=self.buf[-lim:]
    def signal(self)->str:
        lim=max(self.fast,self.slow)+1
        if len(self.buf)<lim: return "hold"
        fp=self._ema(self.buf[:-1], self.fast); sp=self._ema(self.buf[:-1], self.slow)
        fn=self._ema(self.buf, self.fast);  sn=self._ema(self.buf, self.slow)
        if fp<=sp and fn>sn: return "buy"
        if fp>=sp and fn<sn: return "sell"
        return "hold"
