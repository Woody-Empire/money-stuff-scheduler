import logging
import re
from html import unescape

from graph.state import State

logger = logging.getLogger(__name__)


def _html_to_text(s: str) -> str:
    """Strip HTML tags and decode entities."""
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def extract_things_happen(state: State) -> dict:
    html = state["rss_content"]

    marker = "Things happen</h2>"
    marker_pos = html.find(marker)

    if marker_pos == -1:
        logger.warning("未找到 Things Happen 部分")
        return {
            "things_happen_text": "",
            "things_happen_links": [],
            "body_content": html,
        }

    # Locate the <p>...</p> block right after the h2
    p_start = html.find("<p", marker_pos + len(marker))
    p_end = html.find("</p>", p_start)
    p_html = html[p_start : p_end + 4]

    things_text = _html_to_text(p_html)

    # Extract <a> links from the paragraph
    links = []
    search_from = 0
    while True:
        a_start = p_html.find("<a ", search_from)
        if a_start == -1:
            break
        a_end = p_html.find("</a>", a_start)
        a_tag = p_html[a_start : a_end + 4]
        href_match = re.search(r'href="([^"]*)"', a_tag)
        url = href_match.group(1) if href_match else ""
        text = _html_to_text(a_tag)
        if text and url:
            links.append({"text": text, "url": url})
        search_from = a_end + 4

    # Remove Things Happen section from body content
    h2_start = html.rfind("<h2", 0, marker_pos + len(marker))
    if h2_start == -1:
        h2_start = marker_pos
    body_content = html[:h2_start] + html[p_end + 4 :]

    logger.info(
        "提取 Things Happen: %d 字符, %d 个链接",
        len(things_text),
        len(links),
    )
    return {
        "things_happen_text": things_text,
        "things_happen_links": links,
        "body_content": body_content,
    }
