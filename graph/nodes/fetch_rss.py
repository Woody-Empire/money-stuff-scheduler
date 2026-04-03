import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta

import feedparser

from graph.state import State

logger = logging.getLogger(__name__)

BJT = timezone(timedelta(hours=8))


def _parse_published(entry) -> str:
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            return datetime(*t[:6], tzinfo=timezone.utc).astimezone(BJT).strftime("%Y-%m-%d")
    return datetime.now(BJT).strftime("%Y-%m-%d")


def _extract_content(entry) -> str:
    if hasattr(entry, "content") and entry.content:
        return entry.content[0].get("value", "")
    return entry.get("summary", "") or entry.get("description", "")


def _extract_summary(entry) -> str:
    title = entry.get("title", "")
    return title[:120] if title else ""


def fetch_rss_entries(since: str | None = None) -> list[dict]:
    feed_url = os.environ["RSS_FEED_URL"]
    feed = feedparser.parse(feed_url)

    if not feed.entries:
        return []

    results = []
    for i, entry in enumerate(feed.entries):
        published = _parse_published(entry)
        if since and published < since:
            continue
        results.append({
            "index": i,
            "title": entry.get("title", f"Money Stuff — {published}"),
            "published": published,
            "summary": _extract_summary(entry),
            "content": _extract_content(entry),
        })

    return results


async def fetch_rss(state: State) -> dict:
    if state.get("rss_content"):
        return {}

    feed_url = os.environ["RSS_FEED_URL"]
    logger.info("正在获取 RSS: %s", feed_url)

    feed = await asyncio.to_thread(feedparser.parse, feed_url)
    if not feed.entries:
        raise ValueError("RSS 中没有找到任何条目")

    entry = feed.entries[0]
    content = _extract_content(entry)
    date = _parse_published(entry)

    logger.info("获取到条目: %s (内容长度: %d)", entry.get("title", "N/A"), len(content))
    return {"rss_content": content, "date": date}
