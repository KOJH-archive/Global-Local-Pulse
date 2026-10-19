from storage.models import now_utc,parse_dt
from services.settings import SETTINGS

def fresh(result):
 return bool(result and 0 <= (now_utc()-parse_dt(result['collected_at'])).total_seconds() < SETTINGS['cache_minutes']*60)
def fallback(previous,statuses):
 return {**previous,'cache_state':'stale','refresh_statuses':statuses,'refresh_failed':True} if previous else None
