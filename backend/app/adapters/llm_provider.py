from app.ports.llm import LLMProvider


class UnconfiguredLLMProvider:
    """默认安全提供方：未配置模型时拒绝外发资料。"""

    def generate(self, prompt: str) -> str:
        raise RuntimeError("尚未配置 AI 模型；当前不会向外部服务发送知识库内容")


class FakeLLMProvider:
    """测试用模型，验证问答编排时不需要真实网络调用。"""

    def generate(self, prompt: str) -> str:
        return "基于检索资料，建议先核对引用内容后再形成工程结论。"
