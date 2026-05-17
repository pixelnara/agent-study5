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

작성 규칙:
1. 초등학생도 이해할 수 있는 말로만 쓸 것
2. 어려운 단어는 절대 쓰지 말 것 (꼭 써야 하면 바로 옆에 쉬운 말로 설명)
3. 한 줄에 한 가지 내용만
4. 전체 700자 이내로 짧게
5. AI, 반도체, 전력, 데이터센터, 2차전지 관련 내용만
6. "오늘 이것만 기억하세요" 한 줄로 마무리

출력 형식:
━━━━━━━━━━━━━━━━━━━━━
[ 오늘의 시장 이야기 ]
━━━━━━━━━━━━━━━━━━━━━

🧠 AI / 반도체 회사들
-

⚡ 전기 / 데이터센터
-

🔋 배터리 회사들
-

🇺🇸 미국 주식 분위기
-

━━━━━━━━━━━━━━━━━━━━━
📌 오늘 이것만 기억하세요
━━━━━━━━━━━━━━━━━━━━━
(딱 한 줄로 오늘의 핵심)"""

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
