#!/usr/bin/env python3
"""
글로벌 일일 브리핑 자동화 시스템
- 매일 오전 9:55 실행 → 오전 10:00 텔레그램 수신 목표
- 전날 10:01 ~ 당일 09:59 의 24시간 데이터를 수집합니다
"""

import sys
import traceback
from datetime import datetime
import pytz

KST = pytz.timezone('Asia/Seoul')


def log(msg: str):
    ts = datetime.now(KST).strftime('%H:%M:%S')
    print(f'[{ts}] {msg}')


def main():
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    log('글로벌 일일 브리핑 생성 시작')
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')

    from agents.market_agent import MarketAgent
    from agents.news_agent import NewsAgent
    from agents.summary_agent import SummaryAgent
    from agents.telegram_agent import TelegramAgent

    telegram = TelegramAgent()

    try:
        # 1단계: 시장 데이터 수집
        log('1/4 시장 데이터 수집 중...')
        market_data = MarketAgent().fetch_all()

        # 2단계: 뉴스 수집
        log('2/4 뉴스 수집 중...')
        news_data = NewsAgent(hours_back=24).fetch_all()

        # 3단계: AI 요약 생성
        log('3/4 AI 브리핑 생성 중...')
        messages = SummaryAgent().generate(market_data, news_data)

        # 4단계: 텔레그램 전송
        log('4/4 텔레그램 전송 중...')
        telegram.send_all(messages)

        log('✅ 브리핑 전송 완료!')

    except Exception as e:
        log(f'❌ 오류 발생: {e}')
        traceback.print_exc()
        try:
            telegram.send_text(
                f'⚠️ 브리핑 생성 중 오류가 발생했습니다.\n\n오류 내용:\n{str(e)[:300]}'
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
