"""Small local-model connectivity check.

This command verifies only the local Ollama fallback. It does not
require Hugging Face, Crossref, or OpenAlex credentials and is intended for
developer machines running a local model server such as Ollama.
"""

from __future__ import annotations

import os

from research_agent.local_llm import LocalLLMGateway


def main() -> None:
    model = os.getenv("LOCAL_LLM_MODEL", "qwen3:4b").strip()
    base_url = os.getenv(
        "LOCAL_LLM_BASE_URL",
        "http://127.0.0.1:11434/api/chat",
    ).strip()

    gateway = LocalLLMGateway(
        base_url=base_url,
        model=model,
        max_tokens=300,
        temperature=0.0,
    )
    output = gateway.generate(
        "Reply in one short sentence confirming that local model inference works."
    )

    print(f"Local model: {model}")
    print(f"Local endpoint: {base_url}")
    print(f"Local inference: OK - {output[:160]}")


if __name__ == "__main__":
    main()
