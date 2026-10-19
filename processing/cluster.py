import os,re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz.fuzz import token_set_ratio
from processing.normalize import normalize, fingerprint, canonical_url
from services.settings import SETTINGS

CATEGORIES={
 '정치·정책':r'election|president|minister|parliament|vote|trump|budget|정치|대통령|국회|정부|선거|예산|首相|選挙|政権|国会|政党|élection|gouvernement|ministre|macron|bundestag|regierung|kanzler|wahl',
 '경제·생활':r'econom|inflation|price|rate|housing|bank|tax|경제|금리|물가|주택|은행|증시|환율|経済|株価|物価|金利|円安|économ|prix|retraite|impôt|wirtschaft|preise|rente|steuer',
 '사회·안전':r'police|crime|strike|protest|health|hospital|immigration|사건|사고|파업|노동|의료|경찰|재판|이민|事件|事故|逮捕|医療|病院|警察|移民|manifestation|grève|santé|polizei|streik|migration',
 '국제·안보':r'war|ukraine|russia|gaza|israel|iran|military|nato|전쟁|외교|군사|북한|우크라|이스라엘|イラン|ガザ|ウクライナ|北朝鮮|戦争|guerre|ukrain|russ|krieg',
 '기후·환경':r'climate|flood|storm|earthquake|typhoon|기후|홍수|태풍|지진|地震|台風|洪水|climat|inondation|klima|hochwasser',
 '기술·산업':r'\bai\b|openai|google|apple|chip|tech|인공지능|반도체|삼성|기술|半導体|人工知能|技術|technolog|industrie',
 '문화·스포츠':r'football|baseball|soccer|match|league|cup|film|music|야구|축구|영화|가수|드라마|野球|試合|映画|音楽|liga|fußball|cinéma|rugby'
}
def category(title):
 for cat,pattern in CATEGORIES.items():
  if re.search(pattern,title,re.I): return cat
 return '기타'

def semantic_matrix(titles):
 from openai import OpenAI
 with OpenAI(timeout=40,max_retries=1) as client:
  result=client.embeddings.create(model=os.getenv('EMBEDDING_MODEL','text-embedding-3-small'),input=titles)
  vectors=[d.embedding for d in sorted(result.data,key=lambda d:d.index)]
 return cosine_similarity(vectors)

def cluster_articles(articles, embedding_fn=None):
 if not articles:return [],'lexical',None
 titles=[a['title'] for a in articles]; normalized=[normalize(t) for t in titles]
 method='문자·단어 유사도'; warning=None
 if embedding_fn or (os.getenv('ENABLE_EMBEDDINGS')=='1' and os.getenv('OPENAI_API_KEY')):
  try:
   matrix=(embedding_fn or semantic_matrix)(titles); method='임베딩 의미 유사도'; threshold=SETTINGS['embedding_threshold']
  except Exception as e:
   warning='임베딩 실패: '+type(e).__name__; matrix=None
 else: matrix=None
 if matrix is None:
  try: matrix=cosine_similarity(TfidfVectorizer(analyzer='char',ngram_range=(2,4),min_df=1).fit_transform(normalized))
  except ValueError: matrix=np.eye(len(articles))
  threshold=SETTINGS['lexical_threshold']
 groups=[]
 for idx,a in enumerate(articles):
  best=None; best_score=0
  for group in groups:
   # Representative AND average linkage prevents chains joining unrelated events.
   similarity=float(matrix[idx,group[0]])
   avg=float(np.mean(matrix[idx,group]))
   if similarity>=threshold and avg>=threshold*0.92 and similarity>best_score:
    best=group;best_score=similarity
  if best is None:groups.append([idx])
  else:best.append(idx)
 return [dict(id=fingerprint('|'.join(sorted(articles[i]['id'] for i in g))),title=articles[g[0]]['title'],articles=[articles[i] for i in g],category=category(' '.join(titles[i] for i in g)),trends=[]) for g in groups],method,warning

def attach_trends(groups,trends):
 for trend in trends:
  keyword=normalize(trend['keyword']);matches=[]
  for g in groups:
   # Only explicit phrase/token matches. No person-only semantic inference.
   titles=[normalize(a['title']) for a in g['articles']]
   related=trend.get('related_news',[])
   linked=any(canonical_url(a['url'])==canonical_url(n['url']) or token_set_ratio(normalize(a['title']),normalize(n['title']))>=92 for a in g['articles'] for n in related)
   if linked or any((keyword in t if re.search(r'[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]',keyword) else bool(re.search(r'(?<!\w)'+re.escape(keyword)+r'(?!\w)',t))) for t in titles):matches.append(g)
  if matches:
   # A keyword may span multiple events. Mark ambiguous and avoid allocating it.
   if len(matches)==1:matches[0]['trends'].append(trend)
  else:
   groups.append(dict(id=fingerprint('trend:'+trend['keyword']),title=(trend.get('related_news') or [{'title':trend['keyword']}])[0]['title'],articles=[],category=category(' '.join([trend['keyword']]+[a['title'] for a in trend.get('related_news',[])])),trends=[trend],trend_only=True))
 return groups

def common_candidates(results):
 rows=[]
 # Conservative same-language overlap only; semantic cross-language is optional.
 issues=[(r['country'],i) for r in results for i in r['issues']]
 titles=[i['title'] for c,i in issues]
 semantic=None
 if titles and os.getenv('ENABLE_EMBEDDINGS')=='1' and os.getenv('OPENAI_API_KEY'):
  try: semantic=semantic_matrix(titles)
  except Exception: pass
 for n,(country,issue) in enumerate(issues):
  countries={country}
  for m,(other,peer) in enumerate(issues):
   if other==country:continue
   same=token_set_ratio(normalize(issue['title']),normalize(peer['title']))>=83
   if same or (semantic is not None and semantic[n,m]>=SETTINGS['embedding_threshold']):countries.add(other)
  if len(countries)>1 and not any(set(r['countries'])==countries and token_set_ratio(normalize(r['title']),normalize(issue['title']))>70 for r in rows):
   rows.append({'title':issue.get('summary',{}).get('title_ko') or issue['title'],'countries':sorted(countries),'method':'임베딩 후보' if semantic is not None else '제목 유사 후보'})
 return rows
