# Level 3：基础 AI 问答——核心编排详解

状态：已完成

这份说明继续沿用前两个阶段的写法：先说明整个项目想完成什么，再说明本阶段解决哪一段，最后把文件、函数和数据流对应起来。

## 1. 这个阶段在整个知识库中的位置

个人 FDE 知识库最终要形成这样的闭环：

```text
资料进入系统
  -> 变成结构化知识
  -> 建立全文和向量索引
  -> 用户提出工程问题
  -> 系统找到相关证据
  -> AI 根据证据回答
  -> 回答可以追溯原文
  -> 用户评价并补充知识
```

前面已经完成：

```text
Level 1：文件 -> 文本 -> 分块 -> 数据库
Level 2：分块 -> FTS5 索引 -> 关键词检索
```

本阶段要完成：

```text
问题 -> 全文检索证据 -> 提示词 -> 模型回答 -> 保存对话和引用
```

本阶段还不是完整的现代 RAG，因为暂时只有全文检索，没有向量检索；但它已经完成了“检索增强生成”的基本业务形状。

## 2. 为什么现在才做 AI 问答

如果先接一个聊天模型，再想办法把资料塞进去，模型可能会回答得很流畅，但无法证明答案来自哪份白皮书，也无法判断它是不是在胡乱补充。

因此我先把顺序固定成：

```text
先检索
  -> 再构造证据上下文
  -> 最后调用模型
```

这个顺序直接对应 FDE 的工作习惯：先找到方案、标准和项目依据，再形成工程判断。模型在这里是“基于资料的助手”，不是知识库本身。

## 3. 本阶段的完整核心编排

```text
用户问题
  -> API 校验问题不为空
  -> ChatService.answer()
  -> SearchService.search()
  -> 问题归一化
  -> FTS5 / LIKE 查找候选分块
  -> 过滤和返回证据
  -> PromptBuilder.build()
  -> LLMProvider.generate()
  -> 创建或复用会话
  -> 保存 user message
  -> 保存 assistant message
  -> 保存 citations
  -> 返回答案和证据
```

代码调用关系：

```text
POST /api/chat
  -> api.chat.chat()
  -> ChatService.answer()
  -> SearchService.search()
  -> SQLiteDocumentRepository.search_chunks()
  -> PromptBuilder.build()
  -> LLMProvider.generate()
  -> SQLiteChatRepository.create_conversation()
  -> SQLiteChatRepository.add_message()
  -> SQLiteChatRepository.add_citations()
```

## 4. 为什么增加 `ChatService`

`api/chat.py` 只知道 HTTP 请求和响应格式，它不应该自己完成检索、拼提示词、调用模型和写数据库。

真正的流程放进 `ChatService.answer()`，因为它是一个完整的业务用例：

```python
def answer(question, conversation_id=None):
    evidence = search_service.search(question)
    prompt = prompt_builder.build(question, evidence)
    content = llm_provider.generate(prompt)
    save question, answer and citations
    return Answer(...)
```

这样以后无论从网页、命令行还是测试调用问答，都能复用同一个业务流程。

## 5. 为什么增加 `PromptBuilder`

提示词不是 API 的职责，也不是模型 Provider 的职责。它是“把检索结果转成模型上下文”的独立步骤。

当前 `PromptBuilder.build()` 做三件事：

1. 把每个分块加上证据编号；
2. 加入文档标题和分块顺序；
3. 明确告诉模型只能基于证据回答，不足时要说明。

当前生成的上下文大致是：

```text
你是个人 FDE 工程知识助手，只能依据给出的证据回答。

问题：工业现场数据采集怎么做？

资料证据：
[证据 1] 现场方案 / 分块 0
边缘网关负责工业现场数据采集。
```

这样做的原因是让“回答边界”成为代码的一部分，而不是依赖用户每次手动提醒模型。

## 6. 为什么定义 `LLMProvider`

当前没有把 OpenAI、国产模型或本地模型 SDK 直接写进 `ChatService`。原因是模型供应商可能变化，而问答业务不应该跟着重写。

因此定义一个最小接口：

```python
class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
```

目前有两个实现：

```text
UnconfiguredLLMProvider
  未配置模型时直接报错，防止资料被默默发送到外部服务

FakeLLMProvider
  测试用模型，不联网，用来验证业务编排
```

未来可以增加：

```text
LocalLLMProvider
OpenAICompatibleProvider
OtherProvider
```

只要它们实现 `generate()`，`ChatService` 不需要变化。

## 7. 为什么增加 conversations、messages、citations 三张表

对话不是一段字符串。未来需要知道：

```text
哪次会话
  -> 用户问了什么
  -> AI 回答了什么
  -> 回答用了哪些分块
```

所以拆成：

```text
conversations
  保存一次连续对话

messages
  保存 user 和 assistant 的每条消息

citations
  把 assistant 消息和文档分块关联起来
```

引用表尤其重要。只保存回答文本而不保存引用，未来无法判断回答依据，也无法实现“点击回答跳转原文”。

## 8. 没有检索到资料时为什么不调用模型

当前编排是：

```python
evidence = search_service.search(question)
if not evidence:
    return "资料库中没有找到足够依据，暂时不能形成可靠回答。"
```

这是一条安全边界。个人 FDE 知识库的目标是基于你的资料学习和判断，而不是让模型在资料为空时凭常识写一段看起来专业的话。

## 9. 当前自然语言问题如何接入全文检索

Level 2 的全文检索需要短关键词，但用户通常会用完整问句。因此 Level 3 使用了轻量归一化：

```text
工业现场数据采集怎么做？
  -> 工业现场数据采集
```

`SearchService._normalize_query()` 目前只去掉常见提问尾词和问号。它不是意图识别，也不是向量语义理解，只是让当前全文检索能够承接自然语言问句。

真正的意图识别和语义召回将在后续加入：

```text
问题分类
  -> 行业、产品、场景和时间抽取
  -> 关键词检索 + 向量检索
  -> 重排序
```

## 10. 当前实现和完整现代 RAG 的差距

当前实现：

```text
Retrieval
  FTS5 + LIKE 全文检索

Augmentation
  PromptBuilder 把检索结果放进上下文

Generation
  LLMProvider 生成回答

Citation
  保存命中的文档分块
```

还缺少：

```text
EmbeddingService
  分块 -> 向量

VectorRepository
  保存和查询向量

HybridRanker
  合并关键词和向量结果

CitationService
  页码、章节、原文定位的专门处理

FeedbackService
  记录回答是否有用和引用是否准确
```

所以现在是“基于全文检索的基础 RAG 问答”，还不是完整的混合检索 RAG。

## 11. 本阶段文件职责

```text
api/chat.py
  接收 HTTP 请求，返回 HTTP 响应

services/chat_service.py
  问答业务总编排

services/search_service.py
  查询归一化、检索和过滤

services/chat_service.py::PromptBuilder
  问题和证据 -> 模型提示词

ports/llm.py
  定义模型 Provider 的替换边界

adapters/llm_provider.py
  未配置模型和测试模型实现

adapters/sqlite_chat_repository.py
  对话、消息、引用持久化

db.py
  创建 conversations、messages、citations 表

main.py
  启动时把搜索服务、问答服务和模型 Provider 组装起来
```

## 12. 当前阶段的准确结论

当前项目已经具备：

```text
资料入库
  -> 文本分块
  -> FTS5 全文索引
  -> 问题检索
  -> 提示词上下文
  -> 可替换模型调用
  -> 对话和引用保存
```

当前项目还不具备：

```text
向量化
向量检索
混合排序
精确页码引用
回答反馈闭环
```

## 13. 验收结果

```text
cd backend
python -m pytest
```

结果：`5 passed`。

本阶段的代码快照提交会记录为 `level-3-chat`，后续如果模型配置不合适，可以回退到本快照重新替换 Provider，而不会影响文档和搜索代码。
