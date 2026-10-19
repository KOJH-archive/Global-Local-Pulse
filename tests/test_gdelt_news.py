import asyncio
import httpx

from collectors.base import Fetcher
from collectors.gdelt_news import collect, parse_articles
from services.settings import COUNTRIES


def test_gdelt_article_list_preserves_observation_time(window):
    payload = {
        "articles": [
            {
                "title": "A broad public issue",
                "url": "https://example.org/story",
                "domain": "example.org",
                "seendate": "20261018T120000Z",
            }
        ]
    }
    articles, rejected = parse_articles(payload, "US", window)
    assert rejected == 0
    assert articles[0]["source"] == "GDELT 기사 목록"
    assert articles[0]["published_at_kind"] == "gdelt_observed_at"


def test_gdelt_article_list_handles_api_error(window):
    async def main():
        f = Fetcher(transport=httpx.MockTransport(lambda r: httpx.Response(503, text="blocked")))
        articles, state = await collect(f, "US", COUNTRIES["US"], window)
        await f.close()
        assert articles == [] and state["state"] == "error"

    asyncio.run(main())
