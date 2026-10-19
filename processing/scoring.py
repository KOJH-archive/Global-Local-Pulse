import math
from collections import Counter
from services.settings import SETTINGS
from storage.models import parse_dt,KST
from processing.normalize import normalize

def rank_issues(groups,window):
 public_weights=SETTINGS.get('public_weights',{'search':0.70,'breadth':0.30})
 media_weights=SETTINGS.get('media_weights',{'coverage':0.60,'diversity':0.25,'persistence':0.15})
 if any(v<0 for v in [*public_weights.values(),*media_weights.values()]) or any(sum(w.values())<=0 for w in (public_weights,media_weights)):
  raise ValueError('가중치는 0 이상이며 각 묶음의 합이 양수여야 합니다.')
 cap=SETTINGS['max_articles_per_publisher']
 raw=[]
 for g in groups:
  publishers=Counter(a['publisher_id'] for a in g['articles'])
  days={parse_dt(a['published_at']).astimezone(KST).date().isoformat() for a in g['articles']}
  traffic=[t['traffic_floor'] for t in g['trends'] if t.get('traffic_floor') is not None]
  breadth=len({normalize(t['keyword']) for t in g['trends']}) if g['trends'] else None
  raw.append(dict(search=max(traffic) if traffic else None,breadth=breadth,coverage=sum(min(n,cap) for n in publishers.values()) if publishers else None,diversity=len(publishers) if publishers else None,persistence=len(days) if days else None))
 maximum={key:max([r[key] for r in raw if r[key] is not None] or [0]) for key in {**public_weights,**media_weights}}
 scored=[]
 for g,r in zip(groups,raw):
  metrics={key:(math.log1p(v)/math.log1p(maximum[key]) if maximum[key] else 0) if v is not None else None for key,v in r.items()}
  public_active=sum(public_weights[k] for k in public_weights if metrics[k] is not None)
  media_active=sum(media_weights[k] for k in media_weights if metrics[k] is not None)
  public_score=100*sum(public_weights[k]*metrics[k] for k in public_weights if metrics[k] is not None)/public_active if public_active else None
  media_score=100*sum(media_weights[k]*metrics[k] for k in media_weights if metrics[k] is not None)/media_active if media_active else None
  score=public_score if public_score is not None else media_score
  pubs=r['diversity'] or 0; both=bool(g['trends'] and pubs>=2)
  confidence='복수 신호 확인' if both else '검색 신호' if g['trends'] else '언론 신호' if pubs>=2 else '근거 부족'
  # Do not pad TOP 5 with one uncorroborated article.
  if confidence=='근거 부족':continue
  series=Counter(parse_dt(a['published_at']).astimezone(KST).date().isoformat() for a in g['articles'])
  tags=(['검색 급상승'] if g['trends'] else [])+(['검색량 미제공'] if g['trends'] and not traffic else [])+(['복수 매체'] if pubs>=2 else [])
  g={**g,'score':round(score,1) if score is not None else None,'score_label':'대중 관심도' if public_score is not None else '언론 보도 확산도','public_interest_score':round(public_score,1) if public_score is not None else None,'media_attention_score':round(media_score,1) if media_score is not None else None,'metrics':metrics,'raw_metrics':r,'available_weight':round(public_active if public_score is not None else media_active,2),'public_weight_available':round(public_active,2),'media_weight_available':round(media_active,2),'ranking_basis':'public_interest' if public_score is not None else 'media_attention','confidence':confidence,'article_count':len(g['articles']),'publisher_count':pubs,'coverage_change':None,'news_series':[{'date':d,'count':n} for d,n in sorted(series.items())],'search_series':[{'observed_at':t['collected_at'],'keyword':t['keyword'],'traffic':t['traffic'],'lower_bound':t['traffic_floor']} for t in g['trends']], 'tags':tags}
  scored.append(g)
 return sorted(scored,key=lambda g:(g['public_interest_score'] is not None,g['public_interest_score'] or 0,g['media_attention_score'] or 0,g['publisher_count']),reverse=True)
