import asyncio
import logging
import uuid
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from graph import money_stuff_app
from graph.nodes.fetch_rss import fetch_rss_entries
from graph.nodes.save_to_local import get_article_list, get_translated_titles, ARTICLES_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

BJT = timezone(timedelta(hours=8))

app = FastAPI(title="Money Stuff")
app.mount("/static", StaticFiles(directory="static"), name="static")

router = APIRouter()

# --- Task Manager ---
tasks: dict[str, dict] = {}
async_tasks: dict[str, asyncio.Task] = {}
tasks_lock = asyncio.Lock()


async def _run_translate_task(task_id: str, entry: dict):
    async with tasks_lock:
        tasks[task_id]["status"] = "running"
    try:
        await money_stuff_app.ainvoke({
            "rss_content": entry["content"],
            "date": entry["published"],
            "title": entry["title"],
        })
        async with tasks_lock:
            tasks[task_id]["status"] = "completed"
        logger.info("翻译完成: %s", entry["title"])
    except asyncio.CancelledError:
        async with tasks_lock:
            tasks[task_id]["status"] = "cancelled"
        logger.info("翻译已取消: %s", entry["title"])
    except Exception as e:
        async with tasks_lock:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["error"] = str(e)
        logger.error("翻译失败 %s: %s", entry["title"], e)
    finally:
        async with tasks_lock:
            async_tasks.pop(task_id, None)


class TranslateRequest(BaseModel):
    since: str
    selected_indices: list[int]


@router.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("static/index.html")


@router.get("/api/rss/pending")
async def get_pending_entries(since: str | None = None):
    if since is None:
        since = datetime.now(BJT).strftime("%Y-%m-%d")

    entries = fetch_rss_entries(since=since)
    translated = get_translated_titles()

    async with tasks_lock:
        translating = {t["title"] for t in tasks.values() if t["status"] in ("pending", "running")}

    result = []
    for e in entries:
        status = None
        if e["title"] in translated:
            status = "translated"
        elif e["title"] in translating:
            status = "translating"
        result.append({
            "index": e["index"],
            "title": e["title"],
            "published": e["published"],
            "summary": e["summary"],
            "status": status,
        })
    return result


@router.post("/api/translate")
async def translate_entries(req: TranslateRequest):
    all_entries = fetch_rss_entries(since=req.since)
    translated = get_translated_titles()

    pending = [e for e in all_entries if e["title"] not in translated]
    selected = [e for e in pending if e["index"] in req.selected_indices]

    task_ids = []
    for entry in selected:
        task_id = uuid.uuid4().hex[:8]
        async with tasks_lock:
            tasks[task_id] = {
                "id": task_id,
                "title": entry["title"],
                "date": entry["published"],
                "status": "pending",
            }
        handle = asyncio.create_task(_run_translate_task(task_id, entry))
        async_tasks[task_id] = handle
        task_ids.append(task_id)

    return {"task_ids": task_ids}


@router.get("/api/tasks")
async def list_tasks():
    async with tasks_lock:
        return list(tasks.values())


@router.post("/api/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    async with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        if task["status"] not in ("pending", "running"):
            raise HTTPException(status_code=400, detail="只能取消等待中或运行中的任务")
        handle = async_tasks.get(task_id)
        if handle:
            handle.cancel()
        else:
            task["status"] = "cancelled"
    return {"ok": True}


@router.delete("/api/tasks/{task_id}")
async def delete_task(task_id: str):
    async with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        if task["status"] in ("pending", "running"):
            raise HTTPException(status_code=400, detail="任务进行中，无法删除")
        del tasks[task_id]
    return {"ok": True}


@router.get("/api/articles")
async def list_articles():
    return get_article_list()


@router.get("/api/articles/{article_id:path}")
async def get_article(article_id: str):
    file_path = ARTICLES_DIR / f"{article_id}.md"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文章不存在")
    return {"markdown": file_path.read_text(encoding="utf-8")}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
