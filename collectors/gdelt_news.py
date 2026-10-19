"""GDELT DOC article-list collector used instead of Google News RSS.

GDELT exposes article metadata and source-country filtering without requiring a
Google News session.  Its ``seendate`` is an observation time, not a publisher
verified publication time; the distinction is preserved on each article.
"""
import calendar
from datetime import datetime, timezone

from collectors.base import status
from processing.normalize import fingerprint, plain, safe_url
from storage.models import iso, now_utc


def parse_seendate(value):
    value = plain(value).strip()
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S", "%Y%m%dT%H%M%S"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def parse_articles(payload, country, window, collected_at=None):
    articles = []
    rejected = 0
    for item in (payload or {}).get("articles", []):
        title = plain(item.get("title"))
        url = item.get("url", "")
        observed = parse_seendate(item.get("seendate"))
        domain = plain(item.get("domain"))
        if not title or not safe_url(url) or not observed or not domain:
            rejected += 1
            continue
        observed_at = iso(observed)
        if not window.contains(observed_at):
            rejected += 1
            continue
        publisher_id = domain.casefold()
        articles.append(
            {
                "id": fingerprint(url),
                "country": country,
                "title": title,
                "url": url,
                "publisher": domain,
                "publisher_id": publisher_id,
                "publisher_url": "https://" + domain,
                "publisher_verified": True,
                # GDELT supplies first-seen time.  Do not present it as a
                # publisher-provided publication timestamp in the UI.
                "published_at": observed_at,
                "published_at_kind": "gdelt_observed_at",
                "collected_at": collected_at or iso(now_utc()),
                "source": "GDELT 기사 목록",
            }
        )
    return articles, rejected


async def collect(fetcher, code, config, window):
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    source_code = config.get("gdelt_code") or config.get("gdelt", "")
    params = {
        "query": f"sourcecountry:{source_code}",
        "mode": "artlist",
        "format": "json",
        "maxrecords": "250",
        "sort": "HybridRel",
        "startdatetime": window.start.strftime("%Y%m%d%H%M%S"),
        "enddatetime": window.end.strftime("%Y%m%d%H%M%S"),
    }
    try:
        response = await fetcher.get(url, params)
        articles, rejected = parse_articles(response.json(), code, window, iso(now_utc()))
        detail = (
            "GDELT source-country 기사 표본; seendate(최초 관측 시각)를 사용하며 "
            f"발행 시각으로 단정하지 않음; 검증 제외 {rejected}건"
        )
        return articles, status(
            "GDELT 기사 목록",
            "ok" if articles else "empty",
            len(articles),
            detail,
            str(response.url),
        )
    except Exception as exc:
        return [], status(
            "GDELT 기사 목록",
            "error",
            detail=f"{type(exc).__name__}: {str(exc)[:160]}",
            url=url,
        )
