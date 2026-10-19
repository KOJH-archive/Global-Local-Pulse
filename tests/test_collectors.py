import asyncio
import httpx
import pytest
from collectors.google_news import parse_news,collect
from collectors.google_trends import parse_trends,traffic_floor
from collectors.base import Fetcher,SourceError
from services.settings import COUNTRIES
NEWS=b'''<rss version="2.0"><channel><title>News</title><item><title>Event &amp; update - Paper</title><link>https://paper.example/story</link><pubDate>Sun, 18 Oct 2026 12:00:00 GMT</pubDate><source url="https://paper.example">Paper</source></item><item><title>bad</title><link>javascript:alert(1)</link></item></channel></rss>'''
def test_metadata_and_rejection():
 articles,rejected=parse_news(NEWS,'GB');assert len(articles)==1 and rejected==1
 assert articles[0]['title']=='Event & update' and articles[0]['publisher_id']=='paper.example'
def test_not_rss():
 with pytest.raises(SourceError):parse_news(b'<html>error</html>','US')
def test_missing_date_not_invented():
 assert parse_news(b'<rss version="2.0"><channel><item><title>X</title><link>https://x.org/a</link></item></channel></rss>','KR')[0]==[]
def test_news_source_fallback():
 a,n=parse_news(NEWS.replace(b'<source url="https://paper.example">Paper</source>',b''),'US',default_publisher='NPR',default_source_url='https://npr.org/rss')
 assert a[0]['publisher_id']=='npr.org'
@pytest.mark.parametrize('text,expected',[('1,000+',1000),('20K+',20000),('1M+',1000000),('',None),('unknown',None)])
def test_traffic_buckets(text,expected):assert traffic_floor(text)==expected
def test_error_status(window):
 async def main():
  f=Fetcher(transport=httpx.MockTransport(lambda r:httpx.Response(403)))
  a,s=await collect(f,'US',COUNTRIES['US'],window,headlines=True);await f.close()
  assert a==[] and s['state']=='error' and '403' in s['detail']
 asyncio.run(main())
def test_trends_links_not_dated_articles():
 xml=b'''<rss version="2.0" xmlns:ht="https://trends.google.com/trending/rss"><channel><item><title>housing</title><pubDate>Sun, 18 Oct 2026 12:00:00 GMT</pubDate><ht:approx_traffic>1000+</ht:approx_traffic><ht:news_item><ht:news_item_title>Housing story</ht:news_item_title><ht:news_item_url>https://x.org/a</ht:news_item_url><ht:news_item_source>X</ht:news_item_source></ht:news_item></item></channel></rss>'''
 a=parse_trends(xml,'GB')[0]
 assert a['traffic']=='1000+' and a['related_news'][0]['published_at'] is None

def test_google_bot_block_is_specific_and_not_retried(window):
 calls=[]
 def handler(request):
  calls.append(request)
  return httpx.Response(503,text='Sorry... your computer or network may be sending automated queries.')
 async def main():
  f=Fetcher(transport=httpx.MockTransport(handler))
  a,s=await collect(f,'KR',COUNTRIES['KR'],window,headlines=True);await f.close()
  assert s['state']=='error' and '자동화 트래픽 차단' in s['detail']
 asyncio.run(main())
 assert len(calls)==1
