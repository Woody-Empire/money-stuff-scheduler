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

    html_body = md_lib.markdown(
        combined,
        extensions=["extra", "nl2br", "sane_lists"],
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "PingFang SC", "Microsoft YaHei", sans-serif;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    line-height: 1.8;
    color: #333;
    background-color: #fafafa;
}}
h1 {{ color: #1a1a1a; border-bottom: 2px solid #333; padding-bottom: 8px; }}
h2 {{ color: #2c2c2c; margin-top: 1.5em; }}
h3 {{ color: #444; }}
a {{ color: #0066cc; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
blockquote {{
    border-left: 4px solid #ddd;
    margin: 1em 0;
    padding: 0.5em 1em;
    color: #666;
    background-color: #f9f9f9;
}}
ul, ol {{ padding-left: 1.5em; }}
li {{ margin-bottom: 0.3em; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 2em 0; }}
sup {{ font-size: 0.8em; }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    today = datetime.now(BJT).strftime("%Y-%m-%d")
    subject = f"Money Stuff - {today}"

    logger.info("HTML 转换完成，主题: %s", subject)
    return {
        "markdown_content": combined,
        "html_content": html_content,
        "subject": subject,
    }
