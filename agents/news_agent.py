"""
뉴스 수집 에이전트
- 무료 RSS 피드를 사용해 24시간 이내 기사를 수집합니다
- 추가 API 키 없이 동작합니다
"""

import feedparser
import calendar
from datetime import datetime, timedelta, timezone
import pytz

KST = pytz.timezone('Asia/Seoul')

# 섹터별 RSS 피드 목록 (모두 무료, API 키 불필요)
RSS_FEEDS = {
    '한국_정치': [
        ('연합뉴스', 'https://www.yna.co.kr/rss/politics.xml'),
        ('한겨레', 'https://www.hani.co.kr/rss/politics/index.xml'),
        ('조선일보', 'https://www.chosun.com/arc/outboundfeeds/rss/category/politics/'),
        ('중앙일보', 'https://rss.joins.com/joins_news_list.xml'),
    ],
    '미국_정치': [
        ('Politico', 'https://rss.politico.com/politics-news.xml'),
        ('NPR Politics', 'https://feeds.npr.org/1014/rss.xml'),
        ('Washington Post', 'https://feeds.washingtonpost.com/rss/politics'),
        ('The Hill', 'https://thehill.com/feed/'),
    ],
    '지정학_세계경제': [
        ('Reuters World', 'https://feeds.reuters.com/reuters/worldnews'),
        ('BBC World', 'http://feeds.bbci.co.uk/news/world/rss.xml'),
        ('AP Top News', 'https://rsshub.app/apnews/topics/apf-topnews'),
        ('South China Morning Post', 'https://www.scmp.com/rss/91/feed'),
        ('Al Jazeera', 'https://www.aljazeera.com/xml/rss/all.xml'),
        ('The Guardian World', 'https://www.theguardian.com/world/rss'),
    ],
    '경제_금융': [
        ('Reuters Business', 'https://feeds.reuters.com/reuters/businessnews'),
        ('CNBC', 'https://www.cnbc.com/id/100003114/device/rss/rss.html'),
        ('MarketWatch', 'http://feeds.marketwatch.com/marketwatch/topstories/'),
        ('Investing.com', 'https://www.investing.com/rss/news.rss'),
        ('Seeking Alpha', 'https://seekingalpha.com/feed.xml'),
    ],
}


class NewsAgent:

    def __init__(self, hours_back: int = 24):
        now = datetime.now(KST)
        self.cutoff = now - timedelta(hours=hours_back)

    def fetch_all(self) -> dict:
        all_news = {}
        for sector, feeds in RSS_FEEDS.items():
            articles = []
            for source_name, url in feeds:
                fetched = self._fetch_feed(url, source_name)
                articles.extend(fetched)
            # 날짜 기준 최신순 정렬 후 섹터당 최대 15개
            articles.sort(key=lambda x: x.get('pub_ts', 0), reverse=True)
            all_news[sector] = articles[:15]
            print(f"  📰 {sector}: {len(all_news[sector])}개 기사 수집")
        return all_news

    def _fetch_feed(self, url: str, source_name: str) -> list:
        try:
            feed = feedparser.parse(url)
            articles = []
            for entry in feed.entries[:12]:
                pub_date, pub_ts = self._parse_date(entry)

                # 24시간 이내 기사만 포함
                if pub_date and pub_date < self.cutoff:
                    continue

                title = entry.get('title', '').strip()
                if not title:
                    continue

                summary = (
                    entry.get('summary', '')
                    or entry.get('description', '')
                ).strip()
                # HTML 태그 간단히 제거
                import re
                summary = re.sub(r'<[^>]+>', '', summary)[:400]

                articles.append({
                    'title': title,
                    'summary': summary,
                    'link': entry.get('link', ''),
                    'source': source_name,
                    'published': pub_date.strftime('%m/%d %H:%M') if pub_date else '날짜불명',
                    'pub_ts': pub_ts,
                })
            return articles
        except Exception as e:
            print(f"    ⚠️ {source_name} 피드 실패: {e}")
            return []

    def _parse_date(self, entry) -> tuple:
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                ts = calendar.timegm(entry.published_parsed)
                dt = datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(KST)
                return dt, ts
        except Exception:
            pass
        return None, 0
