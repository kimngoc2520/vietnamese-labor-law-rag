from typing import Protocol


class Tool(Protocol):
    name: str

    def run(self, input_text: str) -> str: ...
