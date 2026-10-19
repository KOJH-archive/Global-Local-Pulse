"""UI smoke against the collected snapshot; no network or invented production data."""
import json
from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from storage.database import Database
from storage.models import date_window,now_utc,KST

@pytest.fixture
def app(tmp_path,monkeypatch):
 path=Path(__file__).resolve().parents[1]/'data/latest.json'
 if not path.exists():pytest.skip('실데이터 스냅샷을 먼저 수집하세요.')
 data=json.loads(path.read_text())
 # AppTest is deterministic and does not refetch external services.
 import services.pipeline
 monkeypatch.setattr(services.pipeline,'run',lambda codes,window,**kw:{**data,'countries':[r for r in data['countries'] if r['country'] in codes]})
 monkeypatch.delenv('OPENAI_API_KEY',raising=False)
 return AppTest.from_file(str(path.parents[1]/'app.py'),default_timeout=30).run()

def test_six_country_dashboard(app):
 assert not app.exception
 assert app.metric[0].value=='06'
 assert len(app.tabs)==3
 assert any('비활성화' in x.value for x in app.info)

def test_details_open(app):
 app.button[2].click().run()
 assert not app.exception
 assert any('GDELT' in b.label for b in app.button)
 assert len(app.get('link_button'))>0

def test_category_and_theme(app):
 app.selectbox[1].select('경제·생활').run()
 assert not app.exception
 app.toggle[0].set_value(True).run()
 assert not app.exception

def test_country_selection_and_no_countries(app):
 app.multiselect[0].set_value(['KR','JP']).run()
 app.button[0].click().run()
 assert not app.exception and app.metric[0].value=='02'
 app.multiselect[0].set_value([]).run()
 assert any('하나 이상' in w.value for w in app.warning)

def test_refresh_and_period_controls(app):
 app.selectbox[0].select('최근 1일').run()
 assert any('조건이 변경' in w.value for w in app.warning)
 app.button[1].click().run();assert not app.exception
