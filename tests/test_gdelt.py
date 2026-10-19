import asyncio
import httpx
from collectors.base import Fetcher
from collectors.gdelt import collect
from services.settings import COUNTRIES

def test_gdelt_raw_series(window):
 async def main():
  f=Fetcher(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'timeline':[{'series':'Article Count','data':[{'date':'20261018T000000Z','value':12}]}]})))
  r=await collect(f,'election',COUNTRIES['US'],window);await f.close()
  assert r['points'][0]['value']==12 and r['status']['state']=='ok'
  assert 'sourcecountry' in r['query']
 asyncio.run(main())

def test_gdelt_invalid_json_is_failure(window):
 async def main():
  f=Fetcher(transport=httpx.MockTransport(lambda r:httpx.Response(200,text='Please retry later')))
  r=await collect(f,'election',COUNTRIES['US'],window);await f.close()
  assert r['points']==[] and r['status']['state']=='error'
 asyncio.run(main())
