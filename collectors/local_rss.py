import asyncio
from collectors.base import status
from collectors.google_news import parse_news

async def collect(fetcher,code,config,window):
 async def one(source):
  try:
   r=await fetcher.get(source['url'])
   items,rejected=parse_news(r.content,code,default_publisher=source['name'],default_source_url=source['url'])
   items=[{**a,'source':'현지 공개 RSS'} for a in items if window.contains(a['published_at'])]
   return items,status(source['name']+' RSS','ok' if items else 'empty',len(items),f'공개 RSS 대체 수집 · 날짜/링크 검증 제외 {rejected}건',source['url'])
  except Exception as e:return [],status(source['name']+' RSS','error',detail=str(e)[:120],url=source['url'])
 parts=await asyncio.gather(*(one(s) for s in config.get('fallback_rss',[])))
 return [a for p,s in parts for a in p],[s for p,s in parts]
