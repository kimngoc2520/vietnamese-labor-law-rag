from abc import ABC, abstractmethod
import os

import requests
from dotenv import load_dotenv


load_dotenv()


class BaseLLM(ABC):
    """Interface for LLM generation backends."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Generate an answer from a prompt."""
        raise NotImplementedError


class ColabLLM(BaseLLM):
    """LLM client for the Qwen model served from Google Colab."""

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = base_url or os.getenv("COLAB_LLM_URL")
        self.api_key = api_key or os.getenv("COLAB_LLM_API_KEY")
        self.timeout = timeout

        if not self.base_url:
            raise ValueError("COLAB_LLM_URL is not configured")

        if not self.api_key:
            raise ValueError("COLAB_LLM_API_KEY is not configured")

        self.base_url = self.base_url.rstrip("/")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        context: str = "",
        query: str | None = None,
    ) -> str:
        """Generate an answer through the Colab inference server."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "system_prompt": system_prompt or "",
            "context": context,
            "query": query or prompt,
            "max_new_tokens": 128,
        }

        response = requests.post(
            f"{self.base_url}/generate",
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get("answer")

        if not answer:
            raise ValueError(
                "Colab LLM response does not contain a valid 'answer'"
            )

        return answer

def get_llm() -> BaseLLM:
    """Return the configured LLM backend."""

    return ColabLLM()