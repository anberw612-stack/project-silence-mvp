"""
Centralized model configuration for Fortress Phase 1.
"""

import os
from typing import Optional


API_KEY_PLACEHOLDER = "我是API key，把我换掉"
GEMMA_KEY_PLACEHOLDER = "我是Gemma Key，把我换掉"
QWEN_KEY_PLACEHOLDER = "我是Qwen Key，把我换掉"


def _config_value(name: str, default: str) -> str:
    """
    Read configuration from environment first, then Streamlit secrets.
    """
    env_value = os.environ.get(name)
    if env_value:
        return env_value

    try:
        import streamlit as st

        secret_value = st.secrets.get(name)
        if secret_value:
            return str(secret_value)
    except Exception:
        pass

    return default


MINIMAX_API_KEY = _config_value("MINIMAX_API_KEY", API_KEY_PLACEHOLDER)
MINIMAX_BASE_URL = _config_value("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")
MINIMAX_CHAT_MODEL = _config_value("MINIMAX_CHAT_MODEL", "MiniMax-M2.7")
EMBEDDING_API_BASE = _config_value("EMBEDDING_API_BASE", "https://api.siliconflow.cn/v1")
EMBEDDING_API_KEY = _config_value("EMBEDDING_API_KEY", API_KEY_PLACEHOLDER)
EMBEDDING_MODEL_NAME = _config_value("EMBEDDING_MODEL_NAME", "BAAI/bge-m3")
EMBEDDING_BATCH_SIZE = int(_config_value("EMBEDDING_BATCH_SIZE", "64"))
GATEKEEPER_API_BASE = _config_value("GATEKEEPER_API_BASE", "https://api.siliconflow.cn/v1")
GATEKEEPER_API_KEY = _config_value("GATEKEEPER_API_KEY", API_KEY_PLACEHOLDER)
GATEKEEPER_MODEL_NAME = _config_value("GATEKEEPER_MODEL_NAME", "Qwen/Qwen3-Reranker-8B")
GATEKEEPER_INSTRUCTION = (
    "Given a private user query and an anonymous peer insight candidate, "
    "score whether they represent the same core dilemma, emotional intent, "
    "and requested help. Only assign high relevance to truly similar cases."
)
GEMMA_API_BASE = _config_value("GEMMA_API_BASE", "https://generativelanguage.googleapis.com/v1beta/openai/")
GEMMA_API_KEY = _config_value("GEMMA_API_KEY", GEMMA_KEY_PLACEHOLDER)
GEMMA_MODEL_NAME = _config_value("GEMMA_MODEL_NAME", "gemma-4-31b-it")
QWEN_API_BASE = _config_value("QWEN_API_BASE", "https://api.siliconflow.cn/v1")
QWEN_API_KEY = _config_value("QWEN_API_KEY", QWEN_KEY_PLACEHOLDER)
QWEN_MODEL_NAME = _config_value("QWEN_MODEL_NAME", "Qwen/Qwen3.5-397B-A17B")


def _openai_client_class():
    """
    Import the provider SDK only when a live API client is actually needed.
    This keeps tests and release preflight fast and avoids native-extension
    import failures during modules that only read configuration.
    """
    module = __import__("openai", fromlist=["OpenAI"])
    return module.OpenAI


def build_llm_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """
    Create an OpenAI-compatible client configured for MiniMax.
    """
    client_class = _openai_client_class()
    return client_class(
        api_key=api_key or MINIMAX_API_KEY,
        base_url=base_url or MINIMAX_BASE_URL,
    )


def build_embedding_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
):
    """
    Create an OpenAI-compatible client configured for the embedding provider.
    """
    client_class = _openai_client_class()
    return client_class(
        api_key=api_key or EMBEDDING_API_KEY,
        base_url=base_url or EMBEDDING_API_BASE,
    )


def build_provider_client(
    api_key: str,
    base_url: str,
):
    """
    Create an OpenAI-compatible client for an arbitrary provider.
    """
    client_class = _openai_client_class()
    return client_class(
        api_key=api_key,
        base_url=base_url,
    )
