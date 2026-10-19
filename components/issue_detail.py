import asyncio
import pandas as pd
import plotly.express as px
import streamlit as st
from storage.models import parse_dt,Window,KST
from services.pipeline import enrich_async

def issue_detail(issue,result,w):
 summary=issue.get('summary',{});st.subheader(summary.get('title_ko') or issue['title'])
 primary=f"{issue.get('score_label','주목도')} {issue['score']}" if issue.get('score') is not None else '점수 산정 불가'
 st.caption(f"{result['name']} · 국가 내부 {issue['rank']}위 · {issue['confidence']} · {primary} · 대중 관심 {issue.get('public_interest_score','미관측')} · 언론 확산 {issue.get('media_attention_score','미관측')}")
 left,right=st.columns([1.3,1])
 with left:
  if summary.get('status')=='ok':
   for key,label in [('what','무엇이 발생했나'),('recent','최근 변화'),('why','주목받는 이유'),('background','배경')]:
    st.markdown('**'+label+'**');st.write(summary[key]['text']);st.caption('근거: '+', '.join(summary[key]['evidence_ids']) if summary[key]['evidence_ids'] else '확인되지 않음')
  else:st.info(summary.get('reason','확인된 수치와 원문으로 제공됩니다.'))
  st.markdown('**관심도 근거**')
  st.write(f"검색 관심 신호 {issue.get('public_interest_score','미관측')} · 언론 보도 확산 {issue.get('media_attention_score','미관측')} · 기사 {issue['article_count']}건 · 매체 {issue['publisher_count']}개")
  st.caption('검색 관심 신호가 있는 이슈를 우선 순위화했습니다. 국가 간 점수의 절댓값은 비교하지 않습니다.')
  st.caption('이전 기간 대비 보도량 변화: 확인 불가 · 동등한 수집 표본이 필요합니다.')
  for t in issue['trends']:
   st.write(f"검색어: {t['keyword']} · 원천 검색량 구간: {t['traffic'] or '미제공'}")
   st.caption('급상승 시작 '+t['started_at']+' / 수집 '+t['collected_at'])
   st.link_button('Google Trends 원천',t['url'])
  st.markdown('**관련 기사 · 확인된 원문 메타데이터**')
  # Diversify the 5 representative links.
  selected=[];seen=set()
  for a in issue['articles']:
   if a['publisher_id'] not in seen:selected.append(a);seen.add(a['publisher_id'])
  selected=(selected+[a for a in issue['articles'] if a not in selected])[:5]
  for a in selected:
   st.link_button(a['title'],a['url'],width='stretch')
   date_label='최초 관측' if a.get('published_at_kind')=='gdelt_observed_at' else '발행'
   st.caption(f"{a['publisher']} · {date_label} {parse_dt(a['published_at']).astimezone(KST):%Y-%m-%d %H:%M} KST · 수집 {parse_dt(a['collected_at']).astimezone(KST):%m/%d %H:%M} KST · ID {a['id']}")
  if not selected:st.caption('발행 시각까지 확인된 관련 기사가 없습니다.')
  for trend in issue['trends']:
   for a in trend.get('related_news',[])[:5]:
    st.link_button(a['title'],a['url']);st.caption(a['publisher']+' · Trends 연결 기사 / 발행시각 미제공: 보도량에서 제외')
 with right:
  st.markdown('**관측된 기사량**')
  if issue['news_series']:
   fig=px.bar(pd.DataFrame(issue['news_series']),x='date',y='count',labels={'date':'발행일·관측일 · KST','count':'수집 기사 수'},color_discrete_sequence=['#2ba89b'])
   fig.update_layout(height=250,margin=dict(l=0,r=0,t=10,b=0));st.plotly_chart(fig,width='stretch')
   st.caption('GDELT 최초 관측·현지 RSS 발행일 표본만 표시. 값이 없는 날짜를 0건으로 보간하지 않습니다.')
  else:st.caption('날짜가 확인된 뉴스 관측치 없음')
  st.markdown('**검색 관심 관측**')
  if issue['search_series']:
   st.dataframe(issue['search_series'],hide_index=True)
   st.caption('시계열을 구성할 관측치가 부족할 때 추세선을 만들지 않습니다.')
  else:st.caption('검색 신호 미관측 · 관심이 없다는 뜻이 아닙니다.')
  key=f"gdelt_{result['country']}_{issue['id']}_{w['start']}_{w['end']}"
  if st.button('GDELT 보도 확산 확인',key='load_'+key):
   window=Window(parse_dt(w['start']),parse_dt(w['end']),w['reference'],w['mode'],w['days'],w['clipped_future'])
   with st.spinner('GDELT 공개 API 조회 중…'):st.session_state[key]=asyncio.run(enrich_async(issue,result['country'],window))
  if key in st.session_state:
   g=st.session_state[key];st.caption(g['status']['detail'])
   if g['points']:st.plotly_chart(px.line(pd.DataFrame(g['points']),x='date',y='value',markers=True),width='stretch')
   else:st.warning('GDELT 관측치 없음 · '+g['status']['state'])
