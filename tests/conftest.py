import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import pytest
from datetime import date,datetime,timezone
from storage.models import date_window
@pytest.fixture
def window():return date_window(date(2026,10,19),5,now=datetime(2026,10,19,9,tzinfo=timezone.utc))
@pytest.fixture
def article():
 def factory(title='Government approves new housing tax bill',publisher='one.example',id='a',day='2026-10-18'):
  return dict(id=id,country='GB',title=title,url='https://'+publisher+'/'+id,publisher=publisher,publisher_id=publisher,publisher_verified=True,publisher_url='https://'+publisher,published_at=day+'T12:00:00+00:00',collected_at='2026-10-19T09:00:00+00:00',source='test fixture')
 return factory
