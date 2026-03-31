import asyncio
import logging
import sys

from dotenv import load_dotenv

load_dotenv()

from graph import money_stuff_app  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def run():
    await money_stuff_app.ainvoke({})
    logger.info("流水线执行完成")


if __name__ == "__main__":
    if "--schedule" in sys.argv:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = BlockingScheduler(timezone="Asia/Shanghai")
        scheduler.add_job(
            lambda: asyncio.run(run()),
            CronTrigger(hour=10, minute=20, timezone="Asia/Shanghai"),
            id="money_stuff_daily",
            name="money-stuff-daily-job",
        )
        logger.info("定时任务已启动，北京时间 10:20 执行")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("定时任务已停止")
    else:
        asyncio.run(run())
