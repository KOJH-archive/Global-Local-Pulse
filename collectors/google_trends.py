import calendar, re
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
import feedparser
from collectors.base import SourceError,status
from processing.normalize import plain,safe_url
from storage.models import iso,now_utc

def traffic_floor(raw):
    # Lower bound/bucket only. Never reinterpret as an exact count.
    value=raw.replace(',','').replace('+','').strip().upper()
    match=re.fullmatch(r'([\d.]+)\s*([KM]?)',value)
    return float(match[1])*({'':1,'K':1000,'M':1000000}[match[2]]) if match else None

def parse_trends(body,code):
    parsed=feedparser.parse(body)
    if not parsed.version: raise SourceError('RSS 형식이 아닌 응답')
    trends=[]
    related={}
    try:
        root=ET.fromstring(body); ns={'ht':'https://trends.google.com/trending/rss'}
        for item in root.findall('./channel/item'):
            links=[]
            for n in item.findall('ht:news_item',ns):
                url=n.findtext('ht:news_item_url',default='',namespaces=ns)
                title=plain(n.findtext('ht:news_item_title',default='',namespaces=ns))
                publisher=plain(n.findtext('ht:news_item_source',default='',namespaces=ns))
                if safe_url(url) and title and publisher: links.append({'title':title,'url':url,'publisher':publisher,'published_at':None})
            related[plain(item.findtext('title'))]=links
    except ET.ParseError: pass
    for e in parsed.entries:
        dt=e.get('published_parsed'); title=plain(e.get('title'))
        if not dt or not title: continue
        traffic=plain(e.get('ht_approx_traffic',''))
        trends.append(dict(keyword=title,country=code,traffic=traffic or None,traffic_floor=traffic_floor(traffic),started_at=iso(datetime.fromtimestamp(calendar.timegm(dt),timezone.utc)),collected_at=iso(now_utc()),source='Google Trends',url=f'https://trends.google.com/trending?geo={code}',related_queries=[],related_news=related.get(title,[])))
    return trends

async def collect(fetcher,code,window):
    url='https://trends.google.com/trending/rss'
    try:
        r=await fetcher.get(url,{'geo':code})
        items=[t for t in parse_trends(r.content,code) if window.contains(t['started_at'])]
        return items,status('Google Trends','ok' if items else 'empty',len(items),'현재 RSS 관측만 제공; 과거 검색량 복원·0값 대체 없음',str(r.url))
    except Exception as e: return [],status('Google Trends','error',detail=str(e)[:180],url=url)
