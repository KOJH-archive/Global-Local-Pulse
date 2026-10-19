import asyncio,os
from copy import deepcopy
from datetime import timedelta
from collectors.base import Fetcher,status
from collectors import google_trends,gdelt,gdelt_news,local_rss
from processing.normalize import deduplicate
from processing.cluster import cluster_articles,attach_trends,common_candidates
from processing.scoring import rank_issues
from processing.summarize import summarize
from storage.models import now_utc,iso,KST
from storage.database import Database
from services.settings import COUNTRIES
from services.cache import fresh,fallback

async def collect_country(code,window,db,fetcher,force=False,with_ai=False):
 previous=db.latest(code,window.key,healthy=True)
 if not force and fresh(previous):
  result=deepcopy(previous);result['cache_state']='fresh'
  if with_ai:
   for issue in result['issues']:issue['summary']=await asyncio.to_thread(summarize,issue,db)
  return result
 config=COUNTRIES[code]
 current=window.end >= now_utc()-timedelta(minutes=10)
 tasks=[gdelt_news.collect(fetcher,code,config,window)]
 if current:tasks.append(google_trends.collect(fetcher,code,window))
 results=await asyncio.gather(*tasks)
 articles,news_status=results[0];statuses=[news_status]
 if current:trends,trend_status=results[1];statuses.append(trend_status)
 else:
  trends=db.stored_trends(code,window)
  statuses.append(status('Google Trends','stored' if trends else 'unavailable',len(trends),'과거 검색 트렌드는 저장된 관측치만 사용합니다.'))
 # Independent local-news candidates corroborate the broad GDELT article sample.
 local,local_status=await local_rss.collect(fetcher,code,config,window)
 articles+=local;statuses+=local_status
 raw_articles=list(articles);articles=deduplicate(articles)
 groups,method,warning=await asyncio.to_thread(cluster_articles,articles)
 groups=attach_trends(groups,trends)
 ranked=rank_issues(groups,window)
 issues=ranked[:5]
 for rank,issue in enumerate(issues,1):
  issue['rank']=rank
  issue['summary']=await asyncio.to_thread(summarize,issue,db) if with_ai else {'status':'disabled','reason':'AI 요약 비활성화 · 원문 제목 표시'}
 result=dict(country=code,name=config['name'],flag=config['flag'],window_key=window.key,window=window.json(),collected_at=iso(now_utc()),cache_state='live',issues=issues,article_count=len(articles),raw_article_count=len(raw_articles),trend_count=len(trends),publisher_count=len({a['publisher_id'] for a in articles}),statuses=statuses,clustering_method=method,clustering_warning=warning,rankable_count=len(ranked),ranking_basis='public_interest_first',ranking_note='검색 급상승을 주 순위 기준으로 사용하고 GDELT·현지 RSS 보도는 맥락·교차검증으로 표시합니다.',limited_coverage=True)
 db.save(result,{'articles':raw_articles,'trends':trends})
 # Do not silently replace successful partial data with an old snapshot.
 if not articles and not trends and any(s['state']=='error' for s in statuses):
  saved=fallback(previous,statuses)
  if saved:return saved
 return result

async def run_async(codes,window,db=None,force=False,with_ai=False):
 db=db or Database();f=Fetcher()
 try:
  results=await asyncio.gather(*(collect_country(c,window,db,f,force,with_ai) for c in codes))
  return {'generated_at':iso(now_utc()),'window':window.json(),'countries':results,'common':await asyncio.to_thread(common_candidates,results),'data_kind':'live_collected','version':'1.1.0'}
 finally:await f.close()
def run(codes,window,**kwargs):return asyncio.run(run_async(codes,window,**kwargs))
async def enrich_async(issue,code,window):
 f=Fetcher()
 try:return await gdelt.collect(f,issue['trends'][0]['keyword'] if issue['trends'] else issue['title'][:90],COUNTRIES[code],window)
 finally:await f.close()
