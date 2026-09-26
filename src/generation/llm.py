import os
from abc import ABC, abstractmethod

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class BaseLLM(ABC):
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context: str,
        query: str,
    ) -> str:
        pass


class GeminiLLM(BaseLLM):
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY chưa được cấu hình trong .env"
            )

        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        context: str,
        query: str,
    ) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                max_output_tokens=1024,
            ),
        )

        if not response.text:
            raise RuntimeError("Gemini không trả về nội dung.")

        return response.text.strip()


def get_llm() -> BaseLLM:
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider == "gemini":
        return GeminiLLM()

    raise ValueError(
        f"LLM_PROVIDER không được hỗ trợ: {provider}"
    )