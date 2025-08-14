from core.strategy import EmaCross

def test_strategy_no_crash():
    s=EmaCross(2,4)
    for p in [1,2,3,4,5,6,7,8,9]:
        s.push(p)
    sig=s.signal()
    assert sig in ("buy","sell","hold")
