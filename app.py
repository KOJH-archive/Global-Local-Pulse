import asyncio,json,os
from datetime import date
from pathlib import Path
import streamlit as st
from services.environment import load_environment
load_environment()
from services.settings import COUNTRIES,SETTINGS
from services.pipeline import run,enrich_async
from storage.models import date_window,now_utc,parse_dt,KST
from storage.database import Database
from components.country_cards import country_card
from components.issue_detail import issue_detail
from components.comparison import comparison

st.set_page_config(page_title='Global Local Pulse',page_icon='🌐',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
.block-container{max-width:1600px;padding-top:2.2rem}h1{letter-spacing:-1.5px!important;font-size:2.5rem!important}h3{font-size:1.22rem!important}[data-testid="stVerticalBlockBorderWrapper"]{border-radius:16px} .eyebrow{font-size:12px;letter-spacing:2px;color:#3b9b98;font-weight:700}.caption{color:#83919e;font-size:13px}.intro{font-size:17px;color:#83919e;margin-top:-12px;margin-bottom:20px} .status-dot{color:#35b5a2}.stButton button{border-radius:8px} [data-testid="stMetricValue"]{font-size:1.8rem}
</style>''',unsafe_allow_html=True)
head,tools=st.columns([5,1])
with head:
 st.markdown('<div class="eyebrow">LOCAL SIGNALS · GLOBAL PERSPECTIVE</div>',unsafe_allow_html=True)
 st.title('Global Local Pulse')
 st.markdown('<div class="intro">지금, 각국에서는 무엇에 주목하고 있을까요?</div>',unsafe_allow_html=True)
with tools:
 dark=st.toggle('다크 테마',value=False)
 if dark:st.markdown('<style>.stApp{background:#101a27;color:#e1e9f0}[data-testid="stHeader"]{background:#101a27}[data-testid="stVerticalBlockBorderWrapper"]{background:#152131}input,button,summary{color:inherit!important}</style>',unsafe_allow_html=True)
 st.caption('뉴스 × 검색 관심 신호')
with st.container(border=True):
 c1,c2,c3,c4=st.columns([1.3,1.3,2,1.2])
 with c1:reference=st.date_input('조회 기준일 · 한국시간',value=now_utc().astimezone(KST).date(),max_value=now_utc().astimezone(KST).date())
 with c2:period=st.selectbox('조회 기간',['최근 1일','최근 3일','최근 5일','최근 7일','최근 14일','기준일 ±5일'],index=2)
 with c3:codes=st.multiselect('국가',list(COUNTRIES),default=list(COUNTRIES),format_func=lambda c:COUNTRIES[c]['flag']+' '+COUNTRIES[c]['name'])
 with c4:cat=st.selectbox('카테고리',['전체','정치·정책','경제·생활','사회·안전','국제·안보','기후·환경','기술·산업','문화·스포츠','기타'])
 d1,d2,d3=st.columns([1,1,3])
 with d1:go=st.button('조회 · 캐시 사용',type='primary',width='stretch')
 with d2:refresh=st.button('↻ 데이터 새로고침',width='stretch')
 with d3:use_ai=st.checkbox('한국어 AI 요약',value=bool(os.getenv('OPENAI_API_KEY')),disabled=not bool(os.getenv('OPENAI_API_KEY')))
mode='around' if '±' in period else 'recent';days=5 if mode=='around' else int(period.split()[1][:-1])
window=date_window(reference,days,mode)
if not os.getenv('OPENAI_API_KEY'):st.info('AI 한국어 요약 비활성화 · 프로젝트 폴더의 .env에 OPENAI_API_KEY를 입력한 뒤 앱을 재시작하세요.')
else:st.caption('API 키 감지됨 · 한국어 AI 요약을 선택하고 조회하면 제목 번역과 근거 기반 요약을 생성합니다.')
if not codes:st.warning('조회할 국가를 하나 이상 선택하세요.');st.stop()
query_key=(tuple(codes),window.key)
if (go or refresh or 'dataset' not in st.session_state):
 with st.spinner('현지 뉴스·검색 신호를 확인하고 있습니다. 원천 오류가 있으면 별도로 표시합니다.'):
  st.session_state.dataset=run(codes,window,force=refresh,with_ai=use_ai)
  st.session_state.query_key=query_key
  st.session_state.pop('detail',None)
if query_key!=st.session_state.get('query_key'):
 st.warning('조회 조건이 변경됐습니다. 조회 버튼을 눌러 적용하세요. 아래는 이전 조회 결과입니다.')
data=st.session_state.dataset
window_view=data['window']
st.caption(f"조회 범위 {parse_dt(window_view['start']).astimezone(KST):%Y-%m-%d %H:%M} — {parse_dt(window_view['end']).astimezone(KST):%Y-%m-%d %H:%M} KST · 생성 {parse_dt(data['generated_at']).astimezone(KST):%m/%d %H:%M} KST · 뉴스 시각은 발행 시각이며 사건 발생 시각과 다를 수 있습니다.")
if window_view['clipped_future']:st.caption('조회 범위 중 아직 도래하지 않은 시간은 제외했습니다.')
rows=data['countries'];m=st.columns(4)
m[0].metric('관측 국가',f'{len(rows):02d}');m[1].metric('수집 기사',f"{sum(r['article_count'] for r in rows):,}");m[2].metric('검색 급상승 관측',sum(r['trend_count'] for r in rows));m[3].metric('복수 신호 이슈',sum(i['confidence']=='복수 신호 확인' for r in rows for i in r['issues']))
if any(r['cache_state']=='stale' for r in rows):st.warning('일부 원천 재수집 실패: 마지막 정상 결과를 표시합니다. 각 국가의 수집 시각을 확인하세요.')
tabs=st.tabs(['🌐 국가별 레이더','⇄ 국가 비교','데이터 상태·산정 기준'])
with tabs[0]:
 st.caption('국가 내부 TOP 5 · Google Trends 검색 급상승을 주 순위 기준으로 사용하고, GDELT·현지 RSS는 사건 설명·교차검증에 사용합니다. 국민 전체의 관심도 조사 결과는 아닙니다.')
 for start in range(0,len(rows),3):
  columns=st.columns(3)
  for col,result in zip(columns,rows[start:start+3]):
   with col:
    selected=country_card(result,cat)
    if selected:st.session_state.detail=(result['country'],selected)
 if st.session_state.get('detail'):
  code,issue_id=st.session_state.detail
  result=next((r for r in rows if r['country']==code),None)
  issue=next((i for i in result['issues'] if i['id']==issue_id),None) if result else None
  if issue:
   st.divider();issue_detail(issue,result,window_view)
with tabs[1]:comparison(data,cat)
with tabs[2]:
 for r in rows:
  with st.expander(f"{r['flag']} {r['name']} · 기사 {r['article_count']} · {r['cache_state']}"):
   st.caption('수집 시각 '+r['collected_at']+' · 클러스터링 '+r['clustering_method'])
   st.dataframe(r.get('refresh_statuses',r['statuses']),hide_index=True,width='stretch')
   if r.get('clustering_warning'):st.warning(r['clustering_warning'])
 st.markdown('''**검색 기반 대중 관심도와 언론 보도 확산도를 분리합니다. 국가 간 점수의 절댓값은 비교하지 않습니다.**

- 대중 관심도: 검색 급상승 70% · 검색 후보 폭 30%. 검색량 구간이 있으면 그 값을 사용하고, 없으면 검색어 관측 자체만 표시합니다.
- 언론 보도 확산도: 보도 표본량 60% · 매체 다양성 25% · 관측일 지속성 15%. 언론 신호는 순위를 지배하지 않고 사건 설명·교차검증에 사용합니다.
- 수치 지표는 국가 내부 log(1+x)/log(1+최대값) 정규화. 미관측은 결측이며, 확보한 가중치만 재정규화합니다.
- 같은 매체의 기사 기여는 이슈당 최대 2건. 단일 기사만 있고 검색 신호가 없으면 TOP 5에 넣지 않습니다.
- GDELT·RSS는 전수조사가 아닙니다. 매체 선택·언어·수집 범위 편향이 존재합니다. 매체 도메인은 독립 소유관계를 보장하지 않습니다.
- 과거 동등 표본이 없어 이전 기간 대비 보도량 증감률은 제공하지 않습니다. GDELT 기사 목록은 보도 확산 맥락에 사용하고, 최초 관측 시각을 발행 시각으로 단정하지 않습니다.
- 검색량은 원천이 제공한 구간·하한이며 정확한 검색 횟수가 아닙니다. 검색 급상승은 국민 전체 관심도와 다릅니다.
- 의미 기반 클러스터링은 API 키와 ENABLE_EMBEDDINGS=1이 필요합니다. 기본값은 보수적인 문자·단어 유사도입니다.
- 예약 수집은 설정되지 않았습니다. 새로고침하거나 CLI를 실행해야 새 관측치가 저장됩니다.
''')
 st.download_button('조회 결과 JSON 내려받기',json.dumps(data,ensure_ascii=False,indent=2),'global-local-pulse.json','application/json')
st.caption('GLOBAL LOCAL PULSE / v1.1 · 근거를 먼저, 해석은 그다음')
