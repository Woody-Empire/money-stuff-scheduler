import asyncio
import json
import os
import logging
from pathlib import Path

from graph.state import State

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
ARTICLES_DIR = DATA_DIR / "articles"
INDEX_PATH = DATA_DIR / "index.json"


def _ensure_dirs():
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)


def _read_index() -> dict:
    if INDEX_PATH.exists():
        return json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return {"money-stuff": []}


def _write_index(data: dict):
    INDEX_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_entries(raw: list) -> list[dict]:
    result = []
    for e in raw:
        if isinstance(e, str):
            result.append({"id": e, "date": e, "title": f"Money Stuff — {e}"})
        else:
            result.append(e)
    return result


def get_article_list() -> list[dict]:
    index = _read_index()
    return _normalize_entries(index.get("money-stuff", []))


def get_translated_titles() -> set[str]:
    return {a["title"] for a in get_article_list()}


def get_translated_dates() -> list[str]:
    return sorted({a["date"] for a in get_article_list()}, reverse=True)


async def save_to_local(state: State) -> dict:
    _ensure_dirs()

    date = state["date"]
    title = state.get("title", f"Money Stuff — {date}")

    body = state.get("body_translation", "").strip()
    things = state.get("things_happen_translation", "").strip()

    combined = body
    if things:
        combined += "\n\n" + things

    index = _read_index()
    entries = _normalize_entries(index.get("money-stuff", []))

    same_date = [e for e in entries if e["date"] == date]
    seq = len(same_date) + 1
    article_id = f"{date}_{seq}"

    file_path = ARTICLES_DIR / f"{article_id}.md"
    await asyncio.to_thread(file_path.write_text, combined, "utf-8")

    entries.insert(0, {"id": article_id, "date": date, "title": title})
    entries.sort(key=lambda e: e["date"], reverse=True)

    index["money-stuff"] = entries
    _write_index(index)

    logger.info("已保存 money-stuff %s (%s) 到本地", article_id, title)
    return {"markdown_content": combined}
