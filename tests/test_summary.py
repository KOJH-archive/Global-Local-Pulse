from processing.summarize import validate_summary,summarize,FIELDS
from storage.database import Database

def payload(article):
 a=article()
 return {'title_ko':'주택 세법 승인','keywords':['housing'],**{k:{'text':'주택 세법을 승인했다.','kind':'fact','evidence_ids':[a['id']],'quotes':['new housing tax bill']} for k in FIELDS}}

def test_reject_unknown_source(article):
 p=payload(article);p['why']['evidence_ids']=['invented'];assert not validate_summary(p,[article()])
def test_reject_invented_quote(article):
 p=payload(article);p['why']['quotes']=['People are very angry'];assert not validate_summary(p,[article()])
def test_valid_grounding(article):assert validate_summary(payload(article),[article()])
def test_no_key_is_explicit(monkeypatch,tmp_path):
 monkeypatch.delenv('OPENAI_API_KEY',raising=False)
 assert summarize({'articles':[]},Database(tmp_path/'test.sqlite'))['status']=='disabled'

def test_trend_link_used_for_translation_without_inventing_date():
 from processing.summarize import summary_evidence
 issue={'articles':[],'trends':[{'related_news':[{'title':'Central bank holds interest rates','publisher':'Example','url':'https://example.org/rates','published_at':None}]}]}
 evidence=summary_evidence(issue)
 assert len(evidence)==1 and evidence[0]['published_at'] is None
 assert issue['articles']==[]

def test_mock_ai_translates_trend_only_and_caches(tmp_path):
 import json
 from types import SimpleNamespace
 from processing.summarize import summary_evidence
 issue={'articles':[],'trends':[{'related_news':[{'title':'Central bank holds interest rates','publisher':'Example','url':'https://example.org/rates','published_at':None}]}]}
 a=summary_evidence(issue)[0];output={'title_ko':'중앙은행, 기준금리 동결','keywords':['금리']}
 for k in FIELDS:output[k]={'text':'중앙은행이 금리를 동결했습니다.','kind':'fact','evidence_ids':[a['id']],'quotes':['Central bank holds interest rates']}
 class Completions:
  calls=0
  def create(self,**kwargs):
   self.calls+=1
   assert 'published_at' in kwargs['messages'][1]['content']
   return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(output)))])
 completions=Completions();client=SimpleNamespace(chat=SimpleNamespace(completions=completions));db=Database(tmp_path/'test.sqlite')
 first=summarize(issue,db,client=client);second=summarize(issue,db,client=client)
 assert first['status']=='ok' and first['title_ko']=='중앙은행, 기준금리 동결'
 assert first==second and completions.calls==1
 assert first['evidence'][0]['published_at'] is None
