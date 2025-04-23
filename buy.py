
def executebuy_trade():
    
    
    import requests
    import time
    import hmac
    import hashlib

    
    
    # === CONFIG ===
    API_KEY =  '8NSMWap7w6u1cVJdakBE3FTXGwXXrLKybNZ1HF4u3hjew5nuJIBquRAFxRXis97v'
    API_SECRET = 'r3W29WxQq7YOl2bfpwgQfTT3R1jIXbZM9AagBQVZG0u40rbhRmA8ISoD6cSmC2c6'
    BASE_URL = 'https://fapi.binance.com'
    symbol = 'BTCUSDT'
    leverage = 20
    sl_pips = 50
    sl_usdt = 1
    rrr = 2
    RATE_LIMIT = 0.2  # 5 requests per second = 1/5 = 0.2 seconds between requests

    headers = {
        'X-MBX-APIKEY': API_KEY
    }

    def sign(params):
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(API_SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return query_string + f"&signature={signature}"

    def get_price():
        url = f"{BASE_URL}/fapi/v1/ticker/price"
        res = requests.get(url, params={'symbol': symbol})
        return float(res.json()['price'])

    def get_balance():
        timestamp = int(time.time() * 1000)
        params = {
            'timestamp': timestamp
        }
        query = sign(params)
        url = f"{BASE_URL}/fapi/v2/account?{query}"
        res = requests.get(url, headers=headers)
        balances = res.json()['assets']
        for b in balances:
            if b['asset'] == 'USDT':
                return float(b['availableBalance'])
        return 0

    print("🚀 Starting buy order script...")

    price = get_price()
    print(f"💰 Current {symbol} price: {price}")

    sl_distance = sl_pips * 0.01
    tp_distance = sl_distance * rrr
    qty = round(sl_usdt / sl_distance / price, 6)

    sl_price = round(price - sl_distance, 1)
    tp_price = round(price + tp_distance, 1)

    print(f"📏 SL Distance: {sl_distance} | TP Distance: {tp_distance}")
    print(f"📦 Quantity: {qty} | SL: {sl_price} | TP: {tp_price}")

    # Check balance
    margin_needed = sl_usdt
    balance = get_balance()
    if balance < margin_needed:
        print("❌ Insufficient balance!")
        return

    # Set leverage
    lev_url = f"{BASE_URL}/fapi/v1/leverage"
    lev_data = {
        'symbol': symbol,
        'leverage': leverage,
        'timestamp': int(time.time() * 1000)
    }
    lev_query = sign(lev_data)
    lev_res = requests.post(lev_url, headers=headers, data=lev_query)
    print(f"🎚️ Leverage set: {lev_res.json()}")
    
    time.sleep(RATE_LIMIT)  # Ensure respecting Binance's 5 requests/sec rule

    # Place market order
    order_data = {
        'symbol': symbol,
        'side': 'BUY',
        'type': 'MARKET',
        'quantity': qty,
        'timestamp': int(time.time() * 1000)
    }
    order_query = sign(order_data)
    order_url = f"{BASE_URL}/fapi/v1/order"
    order_res = requests.post(order_url, headers=headers, data=order_query)
    print(f"✅ Market order placed: {order_res.json()}")

    time.sleep(RATE_LIMIT)  # Ensure respecting Binance's 5 requests/sec rule

    # SL
    sl_data = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'STOP_MARKET',
        'stopPrice': sl_price,
        'closePosition': True,
        'timestamp': int(time.time() * 1000)
    }
    sl_query = sign(sl_data)
    sl_url = f"{BASE_URL}/fapi/v1/order"
    sl_res = requests.post(sl_url, headers=headers, data=sl_query)
    print(f"🛡️ SL set: {sl_res.json()}")

    time.sleep(RATE_LIMIT)  # Ensure respecting Binance's 5 requests/sec rule

    # TP
    tp_data = {
        'symbol': symbol,
        'side': 'SELL',
        'type': 'TAKE_PROFIT_MARKET',
        'stopPrice': tp_price,
        'closePosition': True,
        'timestamp': int(time.time() * 1000)
    }
    tp_query = sign(tp_data)
    tp_url = f"{BASE_URL}/fapi/v1/order"
    tp_res = requests.post(tp_url, headers=headers, data=tp_query)
    print(f"🎯 TP set: {tp_res.json()}")


