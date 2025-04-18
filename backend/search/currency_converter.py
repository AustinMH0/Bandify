import requests
from time import time
from threading import Lock

class CurrencyConverter:
    _cache = {}
    _cache_lock = Lock()
    _ttl = 60 * 60  # 1 hour

    @classmethod
    def convert_to_usd(cls, currency: str, amount: float) -> float:
        if currency == 'USD':
            return round(amount, 2)

        now = time()

        with cls._cache_lock:
            if currency in cls._cache:
                rate, timestamp = cls._cache[currency]
                if now - timestamp < cls._ttl:
                    return round(amount * rate, 2)

        try:
            url = f'https://hexarate.paikama.co/api/rates/latest/{currency}?target=USD'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                rate = data.get('data', {}).get('mid')
                if rate:
                    with cls._cache_lock:
                        cls._cache[currency] = (rate, now)
                    return round(amount * rate, 2)
        except Exception as e:
            print(f'[CurrencyConverter] Error: {e}')

        return -1
