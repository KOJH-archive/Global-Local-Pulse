from processing.scoring import rank_issues

def group(articles,trends=None):return dict(id='g',title='Event',category='기타',articles=articles,trends=trends or [])
def test_missing_is_none(article,window):
 a=[article(),article(publisher='two.org',id='b',title='Other title')]
 r=rank_issues([group(a)],window)[0]
 assert r['metrics']['search'] is None and r['available_weight']==1.0
 assert r['public_interest_score'] is None and r['media_attention_score'] is not None
 assert r['confidence']=='언론 신호' and r['coverage_change'] is None

def test_not_pad_single_article(article,window):assert rank_issues([group([article()])],window)==[]
def test_publisher_cap(article,window):
 a=[article(id=str(i),title='event '+str(i)) for i in range(20)]+[article(publisher='two.org',id='other')]
 assert rank_issues([group(a)],window)[0]['raw_metrics']['coverage']==3

def test_multiple_signals(article,window):
 t={'keyword':'housing','traffic_floor':1000,'traffic':'1000+','collected_at':'2026-10-19T09:00:00+00:00'}
 r=rank_issues([group([article(),article(publisher='two.org',id='b')],[t])],window)[0]
 assert r['confidence']=='복수 신호 확인' and r['available_weight']==1

def test_trend_only_missing_news(window):
 t={'keyword':'housing','traffic_floor':None,'traffic':None,'collected_at':'2026-10-19T09:00:00+00:00'}
 r=rank_issues([group([],[t])],window)[0]
 assert r['raw_metrics']['coverage'] is None and r['article_count']==0 and r['metrics']['search'] is None
 assert r['public_interest_score']==100.0 and r['ranking_basis']=='public_interest'

def test_public_interest_ranks_before_media_only(article,window):
 trend={'keyword':'housing','traffic_floor':1000,'traffic':'1000+','collected_at':'2026-10-19T09:00:00+00:00'}
 media=[article(id=str(i),publisher='media.example') for i in range(5)] + [article(id='other',publisher='second.example')]
 ranked=rank_issues([group(media),group([article('Housing prices surge','search.example')],[trend])],window)
 assert ranked[0]['ranking_basis']=='public_interest'
 assert ranked[0]['public_interest_score'] is not None
 assert ranked[0]['media_attention_score'] is not None
