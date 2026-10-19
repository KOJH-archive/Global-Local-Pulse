import calendar, email.utils
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
import feedparser
from collectors.base import SourceError, status
from processing.normalize import plain, safe_url, fingerprint
from storage.models import now_utc, iso

def parse_news(body, country, collected_at=None, default_publisher=None, default_source_url=None):
    feed=feedparser.parse(body)
    if not feed.version: raise SourceError('RSS 형식이 아닌 응답')
    result=[]; rejected=0
    for e in feed.entries:
        title=plain(e.get('title')); url=e.get('link',''); source=e.get('source',{})
        publisher=plain(source.get('title','') or default_publisher)
        source_url=source.get('href','') or default_source_url or ''
        if not publisher and ' - ' in title: publisher=title.rsplit(' - ',1)[-1]
        if publisher and title.endswith(' - '+publisher): title=title[:-(len(publisher)+3)]
        dt=e.get('published_parsed') or e.get('updated_parsed')
        if not title or not safe_url(url) or not dt or not publisher:
            rejected+=1; continue
        published=datetime.fromtimestamp(calendar.timegm(dt),timezone.utc)
        if published > now_utc()+timedelta(minutes=5): rejected+=1; continue
        domain=urlparse(source_url).hostname if safe_url(source_url) else None
        result.append(dict(id=fingerprint(url),country=country,title=title,url=url,publisher=publisher,publisher_id=(domain or publisher).casefold(),publisher_url=source_url if safe_url(source_url) else None,publisher_verified=bool(domain),published_at=iso(published),collected_at=collected_at or iso(now_utc()),source='Google News RSS'))
    return result,rejected

async def collect(fetcher, code, config, window, keyword=None, headlines=False):
    base='https://news.google.com/rss' if headlines else 'https://news.google.com/rss/search'
    params={k:config[k] for k in ('hl','gl','ceid')}
    if not headlines:
        # Broaden date boundary by one day; apply exact UTC/KST range locally.
        q=f'after:{(window.start-timedelta(days=1)).date()} before:{(window.end+timedelta(days=1)).date()}'
        params['q']=f'{keyword or ""} {q}'.strip()
    label='Google News'+(f' · {keyword}' if keyword else ' · 주요 뉴스' if headlines else ' · 기간 검색')
    try:
        response=await fetcher.get(base,params)
        articles,rejected=parse_news(response.content,code)
        articles=[a for a in articles if window.contains(a['published_at'])]
        return articles,status(label,'ok' if articles else 'empty',len(articles),f'날짜·출처·링크 검증 제외 {rejected}건; 제한된 RSS 표본',str(response.url))
    except Exception as e: return [],status(label,'error',detail=str(e)[:180],url=base)
