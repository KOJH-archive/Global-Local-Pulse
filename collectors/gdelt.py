from collectors.base import status
from storage.models import parse_dt
async def collect(fetcher,keyword,country_config,window):
    url='https://api.gdeltproject.org/api/v2/doc/doc'
    keyword=' '.join(keyword.replace('"',' ').replace('(',' ').replace(')',' ').split())[:100]
    query=f'"{keyword}" sourcecountry:"{country_config["gdelt"]}"'
    params=dict(query=query,mode='timelinevolraw',format='json',startdatetime=window.start.strftime('%Y%m%d%H%M%S'),enddatetime=window.end.strftime('%Y%m%d%H%M%S'))
    try:
        r=await fetcher.get(url,params); data=r.json()
        series=data.get('timeline',[])
        points=[{'date':x['date'],'value':x['value']} for s in series if 'article' in s.get('series','').lower() for x in s.get('data',[]) if isinstance(x.get('value'),(int,float))]
        return dict(query=query,points=points,status=status('GDELT','ok' if points else 'empty',len(points),'매체 소재국 기준 기사량; 독자 거주국·검색량 아님',str(r.url)))
    except Exception as e: return dict(query=query,points=[],status=status('GDELT','error',detail=type(e).__name__+': '+str(e)[:100],url=url))
