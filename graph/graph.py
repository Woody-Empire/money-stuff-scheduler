from langgraph.graph import END, START, StateGraph

from graph.nodes import (
    convert_to_html,
    extract_things_happen,
    fetch_rss,
    publish_to_pages,
    translate_body,
    translate_things_happen,
)
from graph.state import State

graph = StateGraph(State)

graph.add_node("fetch_rss", fetch_rss)
graph.add_node("extract_things_happen", extract_things_happen)
graph.add_node("translate_things_happen", translate_things_happen)
graph.add_node("translate_body", translate_body)
graph.add_node("convert_to_html", convert_to_html)
graph.add_node("publish_to_pages", publish_to_pages)

graph.add_edge(START, "fetch_rss")
graph.add_edge("fetch_rss", "extract_things_happen")
# Fan-out: both translation nodes run in parallel
graph.add_edge("extract_things_happen", "translate_things_happen")
graph.add_edge("extract_things_happen", "translate_body")
# Fan-in: wait for both translations before converting
graph.add_edge("translate_things_happen", "convert_to_html")
graph.add_edge("translate_body", "convert_to_html")
graph.add_edge("convert_to_html", "publish_to_pages")
graph.add_edge("publish_to_pages", END)

money_stuff_app = graph.compile()
