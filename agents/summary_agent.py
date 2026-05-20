"""
AI 요약 에이전트
- Claude API를 사용해 수집된 데이터를 브리핑 형식으로 요약합니다
"""

import anthropic
from datetime import datetime
import pytz
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ANTHROPIC_API_KEY

KST = pytz.timezone('Asia/Seoul')


class SummaryAgent:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate(self, market_data: dict, news_data: dict):
        """시장 데이터와 뉴스를 받아 텔레그램 메시지 목록을 반환합니다."""

        # 메시지 1: 시장 현황 (구조화된 숫자 데이터)
        market_msg = self._build_market_message(market_data)

        # 메시지 2: AI 뉴스 요약
        news_msg = self._generate_news_summary(market_data, news_data)

        return [market_msg, news_msg]

    # ──────────────────────────────────────────────
    # 시장 현황 메시지 빌더
    # ──────────────────────────────────────────────

    def _build_market_message(self, market_data: dict) -> str:
        now = datetime.now(KST)
        lines = [
            f"📊 글로벌 일일 브리핑  {now.strftime('%Y.%m.%d %H:%M')}",
            "━━━━━━━━━━━━━━━━━━━━━",
            "[ 시장 현황 ]",
            "━━━━━━━━━━━━━━━━━━━━━",
        ]

        # 미국 증시
        if market_data.get('us_stocks'):
            lines.append('')
            lines.append('🇺🇸 미국 증시 (전일 종가)')
            for name, d in market_data['us_stocks'].items():
                lines.append(self._fmt_price_line(name, d))

        # 가상자산
        if market_data.get('crypto'):
            lines.append('')
            lines.append('₿ 가상자산')
            for name, d in market_data['crypto'].items():
                emoji = '🟢' if d['change_pct'] >= 0 else '🔴'
                arrow = '▲' if d['change_pct'] >= 0 else '▼'
                krw = d['price_krw']
                krw_str = f"{krw/10000:.0f}만원" if krw >= 10000 else f"{krw:,.0f}원"
                lines.append(
                    f"{emoji} {name}: ${d['price']:,.0f} ({krw_str}) {arrow}{abs(d['change_pct']):.2f}%"
                )

        # 환율
        if market_data.get('forex'):
            lines.append('')
            lines.append('💱 환율')
            for name, d in market_data['forex'].items():
                lines.append(self._fmt_price_line(name, d, show_pct=False))

        # 원자재
        if market_data.get('commodities'):
            lines.append('')
            lines.append('🛢️ 원자재')
            for name, d in market_data['commodities'].items():
                lines.append(self._fmt_price_line(name, d))

        # 거시지표
        if market_data.get('macro'):
            lines.append('')
            lines.append('📉 거시지표')
            for name, d in market_data['macro'].items():
                lines.append(self._fmt_price_line(name, d))

        return '\n'.join(lines)

    def _fmt_price_line(self, name: str, d, show_pct: bool = True) -> str:
        if not d:
            return f"  • {name}: 데이터 없음"
        emoji = '🟢' if d['change_pct'] >= 0 else '🔴'
        arrow = '▲' if d['change_pct'] >= 0 else '▼'
        price_str = f"{d['price']:,.2f}"
        if show_pct:
            return f"{emoji} {name}: {price_str} {arrow}{abs(d['change_pct']):.2f}%"
        return f"  • {name}: {price_str}"

    # ──────────────────────────────────────────────
    # Claude AI 뉴스 요약 생성
    # ──────────────────────────────────────────────

    def _generate_news_summary(self, market_data: dict, news_data: dict) -> str:
        market_text = self._market_to_text(market_data)
        news_text = self._news_to_text(news_data)

        prompt = f"""당신은 초등학생에게 오늘 주식 시장을 설명해주는 선생님입니다.
아래 데이터를 보고 아주 쉽고 짧게 설명해주세요.

=== 오늘의 시장 데이터 ===
{market_text}

=== 지난 24시간 주요 뉴스 ===
{news_text}

작성 목표:
"진짜 중요한 시장 뉴스만"
"초등학생도 이해 가능하게"
"투자 흐름이 느껴지게"

작성 규칙:
초등학생도 이해할 수 있는 쉬운 말만 사용
어려운 단어는 괄호로 쉬운 설명 추가
뉴스 원문을 복사하지 말고 쉽게 다시 설명
AI / 반도체 / 전력 / 데이터센터 / 2차전지 관련 뉴스만 사용
시장 영향이 작은 뉴스는 제외
같은 표현 반복 금지
뉴스가 없으면 억지로 채우지 말고 해당 섹션 생략 가능
"왜 중요한지" 한 줄 추가
투자자들이 무엇을 걱정하거나 기대하는지도 포함
전체 550자 이내

출력 스타일:
한 줄에 한 내용만
모바일에서 읽기 쉽게 짧게 작성
뉴스 요약 느낌보다 "오늘 시장 분위기 설명" 느낌으로 작성

출력 형식:
━━━━━━━━━━━━━━━━━━━━━
[ 오늘의 시장 이야기 ]
━━━━━━━━━━━━━━━━━━━━━

🧠 AI / 반도체 회사들

⚡ 전기 / 데이터센터

🔋 배터리 회사들

🇺🇸 미국 주식 분위기

━━━━━━━━━━━━━━━━━━━━━
📌 오늘 이것만 기억하세요
━━━━━━━━━━━━━━━━━━━━━
(오늘 시장 핵심을 한 문장으로 정리)"""

        message = self.client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=2500,
            messages=[{'role': 'user', 'content': prompt}],
        )

        return message.content[0].text

    def _market_to_text(self, market_data: dict) -> str:
        lines = []
        sections = [
            ('미국 증시', 'us_stocks'),
            ('가상자산', 'crypto'),
            ('환율', 'forex'),
            ('원자재', 'commodities'),
            ('거시지표', 'macro'),
        ]
        for label, key in sections:
            group = market_data.get(key, {})
            if group:
                lines.append(f'[{label}]')
                for name, d in group.items():
                    if d:
                        pct = d.get('change_pct', 0)
                        price = d.get('price', d.get('price_usd', 0))
                        lines.append(f'  {name}: {price:,.2f} ({pct:+.2f}%)')
        return '\n'.join(lines)

    def _news_to_text(self, news_data: dict) -> str:
        lines = []
        for sector, articles in news_data.items():
            if articles:
                lines.append(f'\n[{sector}]')
                for article in articles[:8]:
                    lines.append(f'  - [{article["source"]}] {article["title"]}')
                    if article.get('summary'):
                        lines.append(f'    {article["summary"][:200]}')
        return '\n'.join(lines)
