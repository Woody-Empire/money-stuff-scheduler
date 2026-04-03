from typing import TypedDict


class State(TypedDict):
    rss_content: str
    things_happen_text: str
    things_happen_links: list[dict]
    body_content: str
    things_happen_translation: str
    body_translation: str
    markdown_content: str
    date: str
    title: str
