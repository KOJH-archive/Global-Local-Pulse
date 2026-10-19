import asyncio
from storage.database import Database
from services.pipeline import collect_country
from services.cache import fresh,fallback
from storage.models import now_utc,iso
from collectors.base import status
from collectors import gdelt_news,google_trends,local_rss

def test_stale_fallback_only_same_query(tmp_path,window,monkeypatch):
 db=Database(tmp_path/'db.sqlite');old=dict(country='US',window_key=window.key,collected_at=iso(now_utc()),issues=[{'title':'last verified'}],statuses=[],cache_state='live')
 db.save(old,{'articles':[],'trends':[]})
 async def bad(*a,**k):return [],status('test','error',detail='timeout')
 async def bad_local(*a,**k):return [],[status('local','error')]
 monkeypatch.setattr(gdelt_news,'collect',bad);monkeypatch.setattr(google_trends,'collect',bad);monkeypatch.setattr(local_rss,'collect',bad_local)
 result=asyncio.run(collect_country('US',window,db,None,force=True))
 assert result['cache_state']=='stale' and result['issues'][0]['title']=='last verified' and result['refresh_failed']
 assert db.latest('US','different-key',healthy=True) is None

def test_fresh_cache_no_network(tmp_path,window):
 db=Database(tmp_path/'db.sqlite');old=dict(country='US',window_key=window.key,collected_at=iso(now_utc()),issues=[{'title':'last verified'}])
 db.save(old,{})
 result=asyncio.run(collect_country('US',window,db,None));assert result['cache_state']=='fresh'

def test_history_and_raw_stored_separately(tmp_path):
 db=Database(tmp_path/'db.sqlite')
 r=dict(country='KR',window_key='w',collected_at=iso(now_utc()),issues=[])
 db.save(r,{'articles':[{'title':'original'}]});db.save(r,{'articles':[]})
 with db.connect() as c:
  assert c.execute('select count(*) from snapshots').fetchone()[0]==2
  assert c.execute('select count(*) from raw_responses').fetchone()[0]==2
