from dataclasses import dataclass


@dataclass(frozen=True)
class Answer:
    """问答服务向 API 返回的稳定结果。"""

    conversation_id: str
    message_id: str
    content: str
    citations: list[dict]


class PromptBuilder:
    """把检索证据转换为模型上下文，并明确回答边界。"""

    def build(self, question: str, evidence: list[dict]) -> str:
        context = "\n\n".join(
            f"[证据 {index}] {item['title']} / 分块 {item['sequence']}\n{item['content']}"
            for index, item in enumerate(evidence, start=1)
        )
        return (
            "你是个人 FDE 工程知识助手。只能依据给出的证据回答；证据不足时明确说明。"
            "不要捏造标准、参数或项目事实。回答末尾列出使用的证据编号。\n\n"
            f"问题：{question}\n\n资料证据：\n{context}"
        )


class ChatService:
    """问答主编排：检索证据后才允许调用模型，并保存引用。"""

    def __init__(self, search_service, chat_repository, llm_provider, prompt_builder=None):
        self.search_service = search_service
        self.chat_repository = chat_repository
        self.llm_provider = llm_provider
        self.prompt_builder = prompt_builder or PromptBuilder()

    def answer(self, question: str, conversation_id: str | None = None) -> Answer:
        """问题 -> 检索 -> 生成 -> 引用 -> 持久化。"""
        evidence = self.search_service.search(question)
        if not evidence:
            content = "资料库中没有找到足够依据，暂时不能形成可靠回答。"
        else:
            content = self.llm_provider.generate(self.prompt_builder.build(question, evidence))
        conversation_id = conversation_id or self.chat_repository.create_conversation(question[:60])
        self.chat_repository.add_message(conversation_id, "user", question)
        message_id = self.chat_repository.add_message(conversation_id, "assistant", content)
        self.chat_repository.add_citations(message_id, evidence)
        return Answer(conversation_id, message_id, content, evidence)
