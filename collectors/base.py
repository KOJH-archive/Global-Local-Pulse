import asyncio, os
from datetime import datetime
import httpx
from storage.models import now_utc, iso
class SourceError(RuntimeError): pass
class Fetcher:
    def __init__(self, transport=None):
        self.client = httpx.AsyncClient(timeout=float(os.getenv('PULSE_TIMEOUT', '20')), follow_redirects=True, transport=transport, headers={'User-Agent':'GlobalLocalPulse/1.1 RSS research reader', 'Accept':'application/rss+xml, application/xml, application/json, text/xml;q=0.9'})
        self.limit = asyncio.Semaphore(4)
    async def get(self, url, params=None):
        async with self.limit:
            for attempt in range(2):
                try:
                    r = await self.client.get(url, params=params)
                    if r.status_code in (403,429,503) and any(term in r.text.lower() for term in ('may be sending automated queries','unusual traffic from your computer network')):
                        raise SourceError(f'HTTP {r.status_code} · Google 자동화 트래픽 차단: 현재 네트워크의 요청을 거부했습니다. 즉시 재시도하지 않고 대체 RSS를 사용합니다.')
                    if r.status_code in (429, 502, 503, 504) and attempt == 0:
                        await asyncio.sleep(1); continue
                    r.raise_for_status()
                    if len(r.content) > 6_000_000: raise SourceError('응답 크기 제한 초과')
                    return r
                except httpx.HTTPStatusError as e: raise SourceError(f'HTTP {e.response.status_code}') from None
                except httpx.RequestError as e:
                    if attempt == 0: continue
                    raise SourceError(type(e).__name__) from None
    async def close(self): await self.client.aclose()
def status(source, state, count=0, detail='', url=''):
    return dict(source=source, state=state, count=count, detail=detail, url=url, collected_at=iso(now_utc()))
