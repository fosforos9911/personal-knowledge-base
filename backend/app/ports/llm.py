from typing import Protocol


class LLMProvider(Protocol):
    """模型提供方协议，业务层不绑定具体厂商或模型 SDK。"""

    def generate(self, prompt: str) -> str: ...
