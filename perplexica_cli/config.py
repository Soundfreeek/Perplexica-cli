"""Configuration management for Perplexica CLI."""

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = Path.home() / ".config" / "perplexica-cli"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "url": "http://localhost:3000",
    "chat_model": {
        "provider_id": "",
        "key": "",
    },
    "embedding_model": {
        "provider_id": "",
        "key": "",
    },
    "optimization_mode": "balanced",
    "sources": ["web"],
}


def load_config() -> dict[str, Any]:
    """Load config from disk, returning defaults if not found."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            stored = json.load(f)
        merged = {**DEFAULT_CONFIG, **stored}
        return merged
    return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def is_configured(config: dict[str, Any]) -> bool:
    """Check if a chat model and embedding model are configured."""
    chat = config.get("chat_model", {})
    embed = config.get("embedding_model", {})
    return bool(chat.get("provider_id") and chat.get("key")
                and embed.get("provider_id") and embed.get("key"))
