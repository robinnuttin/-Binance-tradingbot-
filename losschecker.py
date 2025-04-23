

def monitor_and_close_losing_positions():
    import time
    import hmac
    import hashlib
    import requests
    from urllib.parse import urlencode



    # ============ CONFIGURABLE SETTINGS ============
    API_KEY = '8NSMWap7w6u1cVJdakBE3FTXGwXXrLKybNZ1HF4u3hjew5nuJIBquRAFxRXis97v'
    API_SECRET = 'r3W29WxQq7YOl2bfpwgQfTT3R1jIXbZM9AagBQVZG0u40rbhRmA8ISoD6cSmC2c6'
    LOSS_THRESHOLD_USDT = 3.5  # <-- Change this value anytime

    # ============ BINANCE SETTINGS ============
    BASE_URL = 'https://fapi.binance.com'
    HEADERS = {'X-MBX-APIKEY': API_KEY}

    # ============ HELPER FUNCTIONS ============
    def sign_request(params, secret):
        query_string = urlencode(params)
        signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
        return query_string + '&signature=' + signature

    def get_time_offset():
        # Calculate offset between local time and Binance server time
        local_time = int(time.time() * 1000)
        server_time = requests.get(BASE_URL + '/fapi/v1/time').json()['serverTime']
        return server_time - local_time  # Add this to local time to get synced time

    # ============ MONITOR LOOP ============
    while True:
        try:
            time_offset = get_time_offset()

            synced_time = lambda: int(time.time() * 1000 + time_offset)

            # Get open positions
            params = {'timestamp': synced_time()}
            query = sign_request(params, API_SECRET)
            response = requests.get(BASE_URL + '/fapi/v2/positionRisk?' + query, headers=HEADERS)
            time.sleep(0.21)

            if response.status_code != 200:
                print("❌ Error fetching positions:", response.json())
            else:
                positions = response.json()
                for pos in positions:
                    entry_price = float(pos['entryPrice'])
                    mark_price = float(pos['markPrice'])
                    position_amt = float(pos['positionAmt'])
                    unrealized_pnl = float(pos['unRealizedProfit'])
                    symbol = pos['symbol']

                    if position_amt == 0:
                        continue

                    if unrealized_pnl < -abs(LOSS_THRESHOLD_USDT):
                        print(f"⚠️ Closing {symbol} position with loss {unrealized_pnl:.2f} USDT")
                        side = 'SELL' if position_amt > 0 else 'BUY'

                        order_params = {
                            'symbol': symbol,
                            'side': side,
                            'type': 'MARKET',
                            'quantity': abs(position_amt),
                            'timestamp': synced_time()
                        }
                        query = sign_request(order_params, API_SECRET)
                        order_resp = requests.post(BASE_URL + '/fapi/v1/order?' + query, headers=HEADERS)
                        time.sleep(0.21)

                        if order_resp.status_code == 200:
                            print(f"✅ Closed {symbol} position at market.")
                        else:
                            print("❌ Failed to close position:", order_resp.json())

        except Exception as e:
            print("⚠️ Exception occurred:", str(e))

        # Wait 5 seconds before next check
        time.sleep(5)

# Run it
print("I'M THE WATCHDAG")
