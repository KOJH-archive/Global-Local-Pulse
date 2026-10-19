from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, date, timedelta, time
from zoneinfo import ZoneInfo
UTC = timezone.utc
KST = ZoneInfo('Asia/Seoul')
def now_utc(): return datetime.now(UTC)
def iso(dt): return dt.astimezone(UTC).isoformat()
def parse_dt(s): return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone(UTC)
@dataclass
class Window:
    start: datetime
    end: datetime
    reference: str
    mode: str
    days: int
    clipped_future: bool = False
    @property
    def key(self): return f'{self.reference}:{self.mode}:{self.days}'
    def contains(self, value):
        try: return self.start <= parse_dt(value) < self.end
        except (ValueError, TypeError, AttributeError): return False
    def json(self): return {**asdict(self), 'start': iso(self.start), 'end': iso(self.end)}
def date_window(reference: date, days=5, mode='recent', now=None):
    now = now or now_utc()
    today = now.astimezone(KST).date()
    if reference > today: raise ValueError('미래 날짜는 조회할 수 없습니다.')
    if days not in (1, 3, 5, 7, 14): raise ValueError('지원하지 않는 기간입니다.')
    if mode not in ('recent', 'around'): raise ValueError('지원하지 않는 조회 방식입니다.')
    first = reference - timedelta(days=5 if mode == 'around' else days-1)
    last = reference + timedelta(days=6 if mode == 'around' else 1)
    start = datetime.combine(first, time.min, KST).astimezone(UTC)
    wanted_end = datetime.combine(last, time.min, KST).astimezone(UTC)
    return Window(start, min(wanted_end, now), str(reference), mode, days, wanted_end > now)
