from exchange_mexc import PaperBroker, _slip

def test_paper_roundtrip():
    pb=PaperBroker(10,5)
    o,f = pb.create_market_order("BTC/USDT","buy",0.1,100.0)
    assert pb.pos_qty>0 and pb.cash<10000
    o,f = pb.create_market_order("BTC/USDT","sell",0.1,100.0)
    assert pb.pos_qty==0

def test_slippage():
    assert _slip(100, 10, "buy") > 100
    assert _slip(100, 10, "sell") < 100
