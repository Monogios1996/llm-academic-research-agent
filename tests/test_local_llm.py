"""Unit tests for local inference and hosted-to-local failover."""

import httpx
import pytest

from research_agent.llm import FailoverGateway, LLMProviderError
from research_agent.local_llm import LocalLLMGateway


class StaticGateway:
    def __init__(self, output: str) -> None:
        self.output = output
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        return self.output


class FailingGateway:
    def __init__(self) -> None:
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        raise LLMProviderError("hosted provider unavailable")


def test_local_gateway_uses_native_ollama_chat_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        body = __import__("json").loads(request.content)
        assert body["model"] == "qwen3:4b"
        assert body["messages"][0]["content"].endswith("/no_think")
        assert body["think"] is False
        assert body["stream"] is False
        assert body["options"]["num_predict"] == 700
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "local response"}},
        )

    gateway = LocalLLMGateway(
        base_url="http://127.0.0.1:11434/api/chat",
        model="qwen3:4b",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert gateway.generate("Create a plan.") == "local response"


def test_local_gateway_strips_leaked_thinking_prefix() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": (
                        "<think>internal reasoning that must not be exposed</think>\n"
                        "{\"subtasks\": []}"
                    ),
                }
            },
        )

    gateway = LocalLLMGateway(
        base_url="http://127.0.0.1:11434/api/chat",
        model="qwen3:4b",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    assert gateway.generate("Create a plan.") == '{"subtasks": []}'


def test_local_gateway_surfaces_connection_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    gateway = LocalLLMGateway(
        base_url="http://127.0.0.1:11434/api/chat",
        model="qwen3:4b",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMProviderError, match="check that Ollama is running"):
        gateway.generate("test")


def test_local_gateway_rejects_empty_final_output_after_thinking() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": "<think>reasoning only</think>",
                }
            },
        )

    gateway = LocalLLMGateway(
        base_url="http://127.0.0.1:11434/api/chat",
        model="qwen3:4b",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMProviderError, match="empty final model output"):
        gateway.generate("test")


def test_failover_uses_primary_when_hosted_provider_succeeds() -> None:
    primary = StaticGateway("hosted")
    fallback = StaticGateway("local")
    gateway = FailoverGateway(primary=primary, fallback=fallback)

    assert gateway.generate("test") == "hosted"
    assert primary.calls == 1
    assert fallback.calls == 0
    assert gateway.fallback_count == 0
    assert gateway.last_provider == "primary"


def test_failover_uses_local_gateway_after_provider_error() -> None:
    primary = FailingGateway()
    fallback = StaticGateway("local")
    gateway = FailoverGateway(primary=primary, fallback=fallback)

    assert gateway.generate("test") == "local"
    assert primary.calls == 1
    assert fallback.calls == 1
    assert gateway.fallback_count == 1
    assert gateway.last_provider == "fallback"


def test_failover_does_not_hide_non_provider_errors() -> None:
    class InvalidPromptGateway:
        def generate(self, prompt: str) -> str:
            raise ValueError("bad prompt")

    fallback = StaticGateway("local")
    gateway = FailoverGateway(primary=InvalidPromptGateway(), fallback=fallback)

    with pytest.raises(ValueError, match="bad prompt"):
        gateway.generate("test")

    assert fallback.calls == 0
