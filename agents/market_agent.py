"""
시장 데이터 수집 에이전트
- 미국 증시, 가상자산, 환율, 원자재, 거시지표를 수집합니다
"""

import yfinance as yf
import requests
from datetime import datetime
import pytz

KST = pytz.timezone('Asia/Seoul')


class MarketAgent:

    def fetch_all(self):
        print("  📊 미국 증시 수집 중...")
        us_stocks = self._fetch_yf_group({
            'S&P 500': '^GSPC',
            '나스닥': '^IXIC',
            '다우존스': '^DJI',
            '러셀 2000': '^RUT',
        })

        print("  ₿ 가상자산 수집 중...")
        crypto = self._fetch_crypto()

        print("  💱 환율 수집 중...")
        forex = self._fetch_yf_group({
            'USD/KRW': 'USDKRW=X',
            'USD/JPY': 'USDJPY=X',
            'EUR/USD': 'EURUSD=X',
            'USD/CNY': 'USDCNY=X',
        })

        print("  🛢️ 원자재 수집 중...")
        commodities = self._fetch_yf_group({
            '금 (Gold)': 'GC=F',
            'WTI 원유': 'CL=F',
            '천연가스': 'NG=F',
            '구리': 'HG=F',
        })

        print("  📉 거시지표 수집 중...")
        macro = self._fetch_yf_group({
            '미국 10년 국채금리': '^TNX',
            '미국 2년 국채금리': '^IRX',
            '공포지수 (VIX)': '^VIX',
            '달러지수 (DXY)': 'DX-Y.NYB',
        })

        return {
            'us_stocks': us_stocks,
            'crypto': crypto,
            'forex': forex,
            'commodities': commodities,
            'macro': macro,
            'timestamp': datetime.now(KST).strftime('%Y년 %m월 %d일 %H:%M KST'),
        }

    def _fetch_yf_group(self, symbols: dict) -> dict:
        result = {}
        for name, symbol in symbols.items():
            data = self._get_ticker(symbol, name)
            if data:
                result[name] = data
        return result

    def _get_ticker(self, symbol: str, name: str):
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='5d')
            if hist.empty or len(hist) < 1:
                return None

            latest = hist.iloc[-1]
            prev = hist.iloc[-2] if len(hist) >= 2 else hist.iloc[-1]

            price = float(latest['Close'])
            prev_price = float(prev['Close'])
            change = price - prev_price
            change_pct = (change / prev_price) * 100 if prev_price else 0

            return {
                'name': name,
                'price': price,
                'change': change,
                'change_pct': change_pct,
                'date': hist.index[-1].strftime('%m/%d'),
            }
        except Exception as e:
            print(f"    ⚠️ {name} ({symbol}) 수집 실패: {e}")
            return None

    def _fetch_crypto(self) -> dict:
        try:
            url = 'https://api.coingecko.com/api/v3/simple/price'
            params = {
                'ids': 'bitcoin,ethereum',
                'vs_currencies': 'usd,krw',
                'include_24hr_change': 'true',
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            result = {}
            mapping = {'bitcoin': '비트코인 (BTC)', 'ethereum': '이더리움 (ETH)'}
            for coin_id, display_name in mapping.items():
                if coin_id in data:
                    d = data[coin_id]
                    result[display_name] = {
                        'name': display_name,
                        'price': d.get('usd', 0),
                        'price_krw': d.get('krw', 0),
                        'change_pct': d.get('usd_24h_change', 0),
                    }
            return result
        except Exception as e:
            print(f"    ⚠️ 가상자산 수집 실패: {e}")
            return {}
