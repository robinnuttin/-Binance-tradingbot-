def checkingactivepositionsell():
    import time
    import hmac
    import hashlib
    import requests
    from sell import executesell_trade

    # Hardcoded API credentials
    api_key = '8NSMWap7w6u1cVJdakBE3FTXGwXXrLKybNZ1HF4u3hjew5nuJIBquRAFxRXis97v'
    api_secret = 'r3W29WxQq7YOl2bfpwgQfTT3R1jIXbZM9AagBQVZG0u40rbhRmA8ISoD6cSmC2c6'

    # Binance Futures endpoint for position risk
    url = "https://fapi.binance.com/fapi/v2/positionRisk"

    # Function to generate signature
    def create_signature(query_string, secret):
        return hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    # Function to check active position
    def your_custom_function():
        try:
            timestamp = int(time.time() * 1000)
            query_string = f"timestamp={timestamp}"
            signature = create_signature(query_string, api_secret)

            full_url = f"{url}?{query_string}&signature={signature}"

            headers = {
                "X-MBX-APIKEY": api_key
            }

            response = requests.get(full_url, headers=headers)
            data = response.json()

            if response.status_code == 200:
                for position in data:
                    if float(position['positionAmt']) == 0:
                        
                        print("✅ No active positions.")
                        executesell_trade()
                        return True
                    else:
                        print(f"⚠️ Active position: {position['symbol']} Amount: {position['positionAmt']}")
                        return False
            else:
                print(f"❌ Error fetching positions: {data}")
                return False

        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

    # Test it
    your_custom_function()
