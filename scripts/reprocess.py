"""Reprocess the same saved evidence without refetching or changing collection time."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from storage.database import Database
from storage.models import Window,parse_dt
from processing.cluster import cluster_articles,attach_trends,common_candidates
from processing.normalize import deduplicate
from processing.scoring import rank_issues

def main():
 db=Database();data=json.loads(Path('data/latest.json').read_text())
 for r in data['countries']:
  with db.connect() as conn:
   raw=json.loads(conn.execute('SELECT raw_responses.payload FROM raw_responses JOIN snapshots ON snapshots.id=raw_responses.snapshot_id WHERE country=? AND window_key=? ORDER BY snapshots.id DESC LIMIT 1',(r['country'],r['window_key'])).fetchone()[0])
  w=r['window'];window=Window(parse_dt(w['start']),parse_dt(w['end']),w['reference'],w['mode'],w['days'],w['clipped_future'])
  groups,method,warning=cluster_articles(deduplicate(raw['articles']))
  ranked=rank_issues(attach_trends(groups,raw['trends']),window)
  r['issues']=ranked[:5];r['rankable_count']=len(ranked)
  r['ranking_basis']='public_interest_first'
  r['ranking_note']='검색 급상승을 주 순위 기준으로 사용하고 GDELT·현지 RSS 보도는 맥락·교차검증으로 표시합니다.'
  # The saved evidence predates the GDELT-first collector.  Do not present
  # old Google News errors as an active dependency in the static snapshot.
  r['statuses']=[s for s in r.get('statuses',[]) if not str(s.get('source','')).startswith('Google News')]
  if not any(str(s.get('source','')).startswith('GDELT') for s in r['statuses']):
   r['statuses'].insert(0,{'source':'GDELT 기사 목록','state':'not_collected','count':0,'detail':'기존 저장 증거 재처리본이라 GDELT 재수집은 수행하지 않았습니다. 새로고침 시 GDELT를 우선 시도합니다.','url':'https://api.gdeltproject.org/api/v2/doc/doc','collected_at':r['collected_at']})
  for rank,i in enumerate(r['issues'],1):i.update(rank=rank,summary={'status':'disabled','reason':'API 키 없음 · AI 한국어 요약 비활성화'})
  db.save(r,raw)
 data['common']=common_candidates(data['countries'])
 Path('data/latest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
