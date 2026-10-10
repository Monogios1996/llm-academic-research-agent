"""Tests for SQLite-backed LangGraph checkpoint persistence."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from research_agent.models import AcademicRecord
from research_agent.persistence import SQLiteCheckpointStore


class _State(TypedDict):
    value: int
    record: AcademicRecord


def test_sqlite_checkpoint_survives_store_reopen(tmp_path) -> None:
    path = tmp_path / "checkpoints" / "research.sqlite3"
    store = SQLiteCheckpointStore(path)

    builder = StateGraph(_State)
    builder.add_node(
        "increment",
        lambda state: {
            "value": state["value"] + 1,
            "record": state["record"],
        },
    )
    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)
    graph = builder.compile(checkpointer=store.saver)

    config = {"configurable": {"thread_id": "run-persist-001"}}
    result = graph.invoke(
        {
            "value": 1,
            "record": AcademicRecord(
                title="Checkpointed LLM Planning Study",
                source="OpenAlex",
                url="https://example.org/work",
                abstract="Evidence for persisted workflow state.",
            ),
        },
        config=config,
    )
    assert result["value"] == 2
    assert result["record"].title == "Checkpointed LLM Planning Study"
    store.close()

    reopened = SQLiteCheckpointStore(path)
    try:
        checkpoint = reopened.saver.get_tuple(config)
        assert checkpoint is not None
        values = checkpoint.checkpoint["channel_values"]
        assert values["value"] == 2
        assert isinstance(values["record"], AcademicRecord)
        assert values["record"].title == "Checkpointed LLM Planning Study"
    finally:
        reopened.close()
