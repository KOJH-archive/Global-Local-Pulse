from collections import Counter
import streamlit as st
import plotly.express as px
import pandas as pd

def comparison(data,category):
 st.subheader('같은 시점, 서로 다른 관심')
 st.caption('대중 관심 신호를 주 순위 기준으로 사용하고, 언론 보도 확산은 별도 지표로 표시합니다. 국가별 점수의 절댓값은 비교하지 않습니다.')
 rows=[]
 for r in data['countries']:
  for i in r['issues']:
   if category=='전체' or category==i['category']:rows.append({'국가':r['name'],'순위':i['rank'],'이슈':i.get('summary',{}).get('title_ko') or i['title'],'카테고리':i['category'],'근거':i['confidence'],'대중 관심':i.get('public_interest_score'),'언론 확산':i.get('media_attention_score')})
 if rows:
  frame=pd.DataFrame(rows);st.dataframe(frame,hide_index=True,width='stretch')
  counts=frame.groupby(['국가','카테고리']).size().reset_index(name='이슈 수')
  chart=px.bar(counts,x='국가',y='이슈 수',color='카테고리',title='TOP 5 안의 카테고리 구성',color_discrete_sequence=px.colors.qualitative.Safe)
  chart.update_layout(height=330);st.plotly_chart(chart,width='stretch')
 st.markdown('**여러 국가에서 함께 관측된 이슈 후보**')
 if data['common']:
  st.dataframe(data['common'],hide_index=True,width='stretch')
 else:st.info('현재 근거와 클러스터링 방식으로 확인한 공통 이슈 후보가 없습니다. 서로 다른 언어의 동일 사건을 놓칠 수 있습니다.')
 st.caption('한 국가에서만 관측된 이슈가 그 국가에만 존재한다는 뜻은 아닙니다. 표본에서의 현지 집중 여부만 탐색합니다.')
