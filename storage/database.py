import json,sqlite3,os
from pathlib import Path
from contextlib import contextmanager
from storage.models import iso,now_utc,parse_dt
from services.settings import ROOT
class Database:
 def __init__(self,path=None):
  self.path=Path(path or os.getenv('PULSE_DB',ROOT/'data/pulse.sqlite3'));self.path.parent.mkdir(parents=True,exist_ok=True)
  seed_new=path is None and not os.getenv('PULSE_DB') and not self.path.exists()
  with self.connect() as db:
   db.executescript('''CREATE TABLE IF NOT EXISTS snapshots(id INTEGER PRIMARY KEY, country TEXT, window_key TEXT, collected_at TEXT, result TEXT, healthy INTEGER); CREATE INDEX IF NOT EXISTS lookup_snapshot ON snapshots(country,window_key,collected_at); CREATE TABLE IF NOT EXISTS raw_responses(id INTEGER PRIMARY KEY,snapshot_id INTEGER,payload TEXT); CREATE TABLE IF NOT EXISTS summaries(cache_key TEXT PRIMARY KEY,payload TEXT,created_at TEXT);''')
  if seed_new and (ROOT/'data/seed.json').exists():
   for entry in json.loads((ROOT/'data/seed.json').read_text()):self.save(entry['result'],entry['raw'])
 @contextmanager
 def connect(self):
  with sqlite3.connect(self.path,timeout=20) as db:
   db.execute('PRAGMA journal_mode=WAL');yield db
 def latest(self,country,key,healthy=False):
  with self.connect() as db:
   row=db.execute('SELECT result FROM snapshots WHERE country=? AND window_key=? '+('AND healthy=1 ' if healthy else '')+'ORDER BY id DESC LIMIT 1',(country,key)).fetchone()
  return json.loads(row[0]) if row else None
 def save(self,result,raw):
  with self.connect() as db:
   cur=db.execute('INSERT INTO snapshots(country,window_key,collected_at,result,healthy) VALUES(?,?,?,?,?)',(result['country'],result['window_key'],result['collected_at'],json.dumps(result,ensure_ascii=False),int(bool(result['issues']))))
   db.execute('INSERT INTO raw_responses(snapshot_id,payload) VALUES(?,?)',(cur.lastrowid,json.dumps(raw,ensure_ascii=False)))
 def stored_trends(self,country,window):
  with self.connect() as db:
   rows=db.execute('SELECT raw_responses.payload FROM raw_responses JOIN snapshots ON snapshots.id=raw_responses.snapshot_id WHERE country=?',(country,)).fetchall()
  trends={}
  for row in rows:
   for t in json.loads(row[0]).get('trends',[]):
    if window.contains(t['started_at']):trends[(t['keyword'],t['started_at'])]=t
  return list(trends.values())
 def summary(self,key):
  with self.connect() as db:r=db.execute('SELECT payload FROM summaries WHERE cache_key=?',(key,)).fetchone()
  return json.loads(r[0]) if r else None
 def save_summary(self,key,payload):
  with self.connect() as db:db.execute('INSERT OR REPLACE INTO summaries VALUES(?,?,?)',(key,json.dumps(payload,ensure_ascii=False),iso(now_utc())))
