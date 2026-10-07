"""Unit tests for the Hugging Face live-provider gateway."""

import httpx
import pytest

from research_agent.huggingface import HuggingFaceGateway, LLMProviderError


def test_huggingface_gateway_sends_authenticated_chat_request() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == HuggingFaceGateway.BASE_URL
        assert request.headers["Authorization"] == "Bearer test-token"
        body = __import__("json").loads(request.content)
        assert body["model"] == "example/model:fastest"
        assert body["messages"][0]["content"] == "Create a plan."
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": '{"subtasks": []}'}}
                ]
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gateway = HuggingFaceGateway(
        token="test-token",
        model="example/model:fastest",
        client=client,
    )

    assert gateway.generate("Create a plan.") == '{"subtasks": []}'


def test_huggingface_gateway_surfaces_http_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorised"})

    gateway = HuggingFaceGateway(
        token="bad-token",
        model="example/model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMProviderError, match="inference request failed"):
        gateway.generate("test")


def test_huggingface_gateway_rejects_unexpected_response_shape() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"choices": []})

    gateway = HuggingFaceGateway(
        token="test-token",
        model="example/model",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(LLMProviderError, match="unexpected response structure"):
        gateway.generate("test")


def test_huggingface_gateway_rejects_empty_prompt() -> None:
    gateway = HuggingFaceGateway(
        token="test-token",
        model="example/model",
        client=httpx.Client(transport=httpx.MockTransport(lambda request: None)),
    )

    with pytest.raises(ValueError, match="prompt cannot be empty"):
        gateway.generate("   ")
