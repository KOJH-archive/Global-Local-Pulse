"""Build a read-only web snapshot and portable Python source ZIP (stdlib only)."""
from pathlib import Path
import shutil,zipfile,json
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'
DIRS=['config','collectors','processing','storage','services','components','scripts','tests','web','reports','.streamlit']
FILES=['app.py','requirements.txt','requirements-lock.txt','README.md','DEVELOPMENT_REPORT.md','.env.example','.gitignore','.dockerignore','Dockerfile','run_windows.bat','run.sh','data/latest.json','data/seed.json']
def main():
 DIST.mkdir(exist_ok=True)
 for name in ('index.html','app.js'):shutil.copy2(ROOT/'web'/name,DIST/name)
 shutil.copy2(ROOT/'data/latest.json',DIST/'data.json')
 paths=[ROOT/f for f in FILES if (ROOT/f).is_file()]
 for d in DIRS:
  paths += [p for p in (ROOT/d).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in ('.pyc',)]
 archive=DIST/'global-local-pulse-v1.1.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(set(paths)):
   relative=Path('global-local-pulse')/p.relative_to(ROOT)
   info=zipfile.ZipInfo(str(relative),(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
   z.writestr(info,p.read_bytes())
 print(json.dumps({'source_zip':str(archive),'files':len(paths),'size':archive.stat().st_size}))
if __name__=='__main__':main()
