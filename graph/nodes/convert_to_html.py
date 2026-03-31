import logging
from datetime import datetime, timedelta, timezone

import markdown as md_lib

from graph.state import State

logger = logging.getLogger(__name__)

BJT = timezone(timedelta(hours=8))


def convert_to_html(state: State) -> dict:
    body = state.get("body_translation", "")
    things = state.get("things_happen_translation", "")

    combined = body.strip()
    if things.strip():
        combined += "\n\n" + things.strip()

    html_content = md_lib.markdown(
        combined,
        extensions=["extra", "nl2br", "sane_lists"],
    )

    today = datetime.now(BJT).strftime("%Y-%m-%d")
    subject = f"Money Stuff - {today}"

    logger.info("HTML 转换完成，主题: %s", subject)
    return {
        "markdown_content": combined,
        "html_content": html_content,
        "subject": subject,
    }
