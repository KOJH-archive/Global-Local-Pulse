import numpy as np
from processing.cluster import cluster_articles,attach_trends
from processing.normalize import deduplicate,safe_url

def test_dedup_syndicated_exact_title(article):
 assert len(deduplicate([article(),article(publisher='two.example',id='b')]))==1

def test_same_publisher_fuzzy_duplicate(article):
 assert len(deduplicate([article(),article(title='Government approves new housing tax bill!',id='b')]))==1

def test_unrelated_same_person_not_merge(article,monkeypatch):
 monkeypatch.delenv('ENABLE_EMBEDDINGS',raising=False)
 groups,method,_=cluster_articles([article('Trump discusses hospital funding in congress'),article('Trump watches baseball final with family',id='b')])
 assert len(groups)==2

def test_optional_semantics(article):
 groups,method,_=cluster_articles([article('新しい住宅税法を承認'),article('New housing tax law approved',id='b',publisher='b.org')],embedding_fn=lambda t:np.array([[1,.91],[.91,1]]))
 assert len(groups)==1 and '임베딩' in method

def test_trend_ambiguity_not_allocated(article):
 groups=[{'articles':[article('Trump housing bill')],'trends':[]},{'articles':[article('Trump baseball final')],'trends':[]}]
 attach_trends(groups,[{'keyword':'Trump'}]);assert not any(g['trends'] for g in groups)

def test_trend_only_candidate():
 assert attach_trends([],[{'keyword':'rail strike'}])[0]['articles']==[]

def test_unsafe_link():assert not safe_url('javascript:alert(1)') and not safe_url('https://user:pass@x.org')
