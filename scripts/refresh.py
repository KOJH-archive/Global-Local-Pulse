import sys,argparse,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from services.environment import load_environment
load_environment()
from datetime import date
from storage.models import date_window,now_utc,KST
from services.pipeline import run
from services.settings import COUNTRIES

def main():
 p=argparse.ArgumentParser(description='실제 RSS 수집 · 기본적으로 예약 실행 없음')
 p.add_argument('--countries',nargs='+',choices=list(COUNTRIES),default=list(COUNTRIES));p.add_argument('--date',default=str(now_utc().astimezone(KST).date()));p.add_argument('--days',type=int,default=5);p.add_argument('--around',action='store_true');p.add_argument('--force',action='store_true');p.add_argument('--ai',action='store_true');p.add_argument('--output',default='data/latest.json')
 args=p.parse_args();result=run(args.countries,date_window(date.fromisoformat(args.date),args.days,'around' if args.around else 'recent'),force=args.force,with_ai=args.ai)
 output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2))
 for r in result['countries']:print(f"{r['country']} 기사 {r['article_count']} / 검색어 {r['trend_count']} / TOP {len(r['issues'])} / {r['cache_state']}",flush=True)
 print('Saved:',output)
if __name__=='__main__':main()
