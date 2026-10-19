from datetime import date,datetime,timezone
import pytest
from storage.models import date_window
NOW=datetime(2026,10,19,9,tzinfo=timezone.utc)
def test_recent_kst():
 w=date_window(date(2026,10,19),5,now=NOW)
 assert w.start.isoformat()=='2026-10-14T15:00:00+00:00'
 assert w.end==NOW
 assert not w.contains('2026-10-19T10:00:00+00:00')
def test_around_clips_future():
 w=date_window(date(2026,10,18),5,'around',now=NOW)
 assert w.clipped_future and w.end==NOW
 assert w.start.date()==date(2026,10,12)
def test_historical_no_future():
 w=date_window(date(2026,10,1),3,now=NOW)
 assert w.end.isoformat()=='2026-10-01T15:00:00+00:00'
 assert not w.clipped_future
@pytest.mark.parametrize('days',[1,3,5,7,14])
def test_supported_windows(days):assert date_window(date(2026,10,1),days,now=NOW).days==days
@pytest.mark.parametrize('reference,days',[(date(2026,10,20),5),(date(2026,10,1),2)])
def test_invalid(reference,days):
 with pytest.raises(ValueError):date_window(reference,days,now=NOW)
