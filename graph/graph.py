from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

from graph.nodes import (
    extract_things_happen,
    fetch_rss,
    save_to_local,
    translate_body,
    translate_things_happen,
)
from graph.state import State

graph = StateGraph(State)

retry = RetryPolicy(max_attempts=5, initial_interval=60, backoff_factor=2)

graph.add_node("fetch_rss", fetch_rss, retry=retry)
graph.add_node("extract_things_happen", extract_things_happen)
graph.add_node("translate_things_happen", translate_things_happen, retry=retry)
graph.add_node("translate_body", translate_body, retry=retry)
graph.add_node("save_to_local", save_to_local)

graph.add_edge(START, "fetch_rss")
graph.add_edge("fetch_rss", "extract_things_happen")
# Fan-out: both translation nodes run in parallel
graph.add_edge("extract_things_happen", "translate_things_happen")
graph.add_edge("extract_things_happen", "translate_body")
# Fan-in: wait for both translations before saving
graph.add_edge("translate_things_happen", "save_to_local")
graph.add_edge("translate_body", "save_to_local")
graph.add_edge("save_to_local", END)

money_stuff_app = graph.compile()
