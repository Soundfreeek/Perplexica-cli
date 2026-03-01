"""API client for Perplexica."""

from typing import Any, Generator

import httpx


class PerplexicaAPI:
    """Client for the Perplexica REST API."""

    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=120.0)

    def get_providers(self) -> list[dict[str, Any]]:
        """Fetch available providers and their models."""
        resp = self.client.get("/api/providers")
        resp.raise_for_status()
        return resp.json().get("providers", [])

    def search(
        self,
        query: str,
        chat_model: dict[str, str],
        embedding_model: dict[str, str],
        sources: list[str] | None = None,
        optimization_mode: str = "balanced",
        history: list[list[str]] | None = None,
        system_instructions: str | None = None,
    ) -> dict[str, Any]:
        """Run a non-streaming search query."""
        payload = self._build_payload(
            query, chat_model, embedding_model, sources,
            optimization_mode, history, system_instructions, stream=False,
        )
        resp = self.client.post("/api/search", json=payload)
        resp.raise_for_status()
        return resp.json()

    def search_stream(
        self,
        query: str,
        chat_model: dict[str, str],
        embedding_model: dict[str, str],
        sources: list[str] | None = None,
        optimization_mode: str = "balanced",
        history: list[list[str]] | None = None,
        system_instructions: str | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Run a streaming search query, yielding parsed SSE events."""
        payload = self._build_payload(
            query, chat_model, embedding_model, sources,
            optimization_mode, history, system_instructions, stream=True,
        )
        with self.client.stream("POST", "/api/search", json=payload) as resp:
            resp.raise_for_status()
            import json
            for line in resp.iter_lines():
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                    yield event
                except json.JSONDecodeError:
                    continue

    def _build_payload(
        self,
        query: str,
        chat_model: dict[str, str],
        embedding_model: dict[str, str],
        sources: list[str] | None,
        optimization_mode: str,
        history: list[list[str]] | None,
        system_instructions: str | None,
        stream: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "chatModel": {
                "providerId": chat_model["provider_id"],
                "key": chat_model["key"],
            },
            "embeddingModel": {
                "providerId": embedding_model["provider_id"],
                "key": embedding_model["key"],
            },
            "query": query,
            "sources": sources or ["web"],
            "optimizationMode": optimization_mode,
            "stream": stream,
        }
        if history:
            payload["history"] = history
        if system_instructions:
            payload["systemInstructions"] = system_instructions
        return payload

    def close(self) -> None:
        self.client.close()
