import streamlit as st
from storage.models import parse_dt,KST

def country_card(result,category):
 selected=None
 with st.container(border=True):
  st.subheader(f"{result['flag']} {result['name']}")
  st.caption(f"기사 {result['article_count']} · 검색어 {result['trend_count']} · {parse_dt(result['collected_at']).astimezone(KST):%m/%d %H:%M} KST")
  errors=[s for s in result.get('refresh_statuses',result['statuses']) if s['state']=='error']
  if errors:st.caption(f"⚠ 원천 {len(errors)}건 오류 · 데이터 상태 탭 확인")
  issues=[i for i in result['issues'] if category=='전체' or i['category']==category]
  if not issues:st.info('조건에 맞는 근거가 충분하지 않습니다.')
  for i in issues:
   summary=i.get('summary',{});title=summary.get('title_ko') if summary.get('status')=='ok' else i['title']
   if st.button(f"{i['rank']:02d}  {title}",key=f"issue_{result['country']}_{i['id']}",width='stretch'):selected=i['id']
   scores=[]
   if i.get('public_interest_score') is not None:scores.append(f"대중 관심 {i['public_interest_score']}")
   if i.get('media_attention_score') is not None:scores.append(f"언론 확산 {i['media_attention_score']}")
   st.caption(f"{i['category']} · {' / '.join(i['tags']) or '추가 신호 없음'} · {i['confidence']} · {' · '.join(scores)}")
   if summary.get('status')=='ok':st.write(summary['what']['text'])
   else:st.caption(f"확인된 기사 {i['article_count']}건 · 매체 {i['publisher_count']}곳. "+('검색 급상승 신호와 연결되었습니다.' if i['trends'] else '복수 매체의 제목 유사성으로 묶인 후보입니다.'))
  if len(result['issues'])<5:st.caption('근거가 부족한 항목으로 5개를 채우지 않습니다.')
 return selected
