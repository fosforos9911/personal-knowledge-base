# Level 2：全文检索——核心编排详解

状态：已完成  
Git 快照：`d3aa871 feat: add level 2 full text search`

这份说明专门解释“这一阶段在整个项目中的位置”。它不只是列出新增文件，而是把个人知识库从资料进入到知识改善的完整主线画出来，再说明当前代码已经走到哪一步。

## 1. 先看整个项目真正要完成的事情

你的系统最终不是一个简单的文件上传器，也不是单独的聊天页面。它要形成一个持续循环：

```text
资料进入系统
  -> 变成结构化知识
  -> 建立可检索索引
  -> 用户提出工程问题
  -> 系统准确找到相关证据
  -> AI 根据证据回答
  -> 回答可以追溯原文
  -> 用户评价和补充知识
  -> 知识库继续改善
```

这条链才是个人 FDE 知识库的主业务编排。它可以拆成六个相互衔接的阶段：

```text
1. Ingestion       文档入库
2. Structuring     文本解析、元数据和分块
3. Indexing        全文索引、向量索引
4. Retrieval       根据问题寻找证据
5. Generation      AI 根据证据生成回答
6. Feedback        引用确认、纠错和知识维护
```

## 2. 当前代码到底走到了哪一步

当前工程不是完整 RAG，而是完成了“文档入库 + 结构化分块 + 全文索引”。位置如下：

```text
资料进入系统       已完成（Level 1）
  -> 变成结构化知识 已完成基础版（Level 1）
  -> 全文准确检索   已完成第一版（Level 2）
  -> 向量语义检索   尚未完成（Level 4）
  -> AI 根据资料回答 尚未完成（Level 3）
  -> 回答追溯原文   数据结构已预留，问答引用尚未完成（Level 3）
  -> 用户反馈改善   尚未完成（后续阶段）
```

因此，当前项目处于：

> RAG 的知识准备和关键词检索阶段，还没有进入完整的检索增强生成阶段。

## 3. Level 1 完成的是什么

Level 1 解决的是“如何把一个文件变成系统内部可以处理的知识对象”。编排是：

```text
upload_document()
  -> DocumentService.import_document()
  -> repository.create(document: pending)
  -> repository.mark_status(processing)
  -> file_store.save()
  -> parser_registry.parse()
  -> chunker.split()
  -> repository.replace_chunks()
  -> repository.mark_status(ready)
```

这段流程的重点不是上传本身，而是状态和职责：

- 先创建 `pending`，说明系统已经接收到文档；
- 进入 `processing`，说明正在解析和分块；
- 成功后变成 `ready`，说明可以进入检索；
- 任意一步失败变成 `failed`，以后可以重试。

Level 1 之后，系统中有两类重要数据：

```text
documents
  文档标题、行业、作者、可信等级、项目阶段和处理状态

document_chunks
  文档被切开的正文、顺序和位置
```

为什么要切分？因为一份几十页的白皮书不能每次都全部交给搜索或模型。分块后可以只找相关的几段，也能在回答中指出具体分块。

## 4. Level 2 解决的是什么

Level 1 虽然有了 `document_chunks`，但这些内容只是保存起来，还没有“查找入口”。Level 2 的任务就是建立第一个可用索引：全文检索。

本阶段编排是：

```text
文档分块完成
  -> 读取文档元数据
  -> 将标题、正文、行业、作者、关键词写入 chunk_fts
  -> 用户输入查询词
  -> FTS5 MATCH 查找候选分块
  -> 中文或特殊术语用 LIKE 保底
  -> 按行业、类型、阶段、可信等级过滤
  -> 返回正文和文档定位信息
```

对应代码链路是：

```text
GET /api/search
  -> api.search.search()
  -> SearchService.search()
  -> SQLiteDocumentRepository.search_chunks()
  -> chunk_fts MATCH
  -> LIKE fallback
  -> SearchService._apply_filters()
  -> 返回分块级结果
```

## 5. 为什么有 `chunk_fts`，不直接查 `document_chunks`

`document_chunks` 是知识内容表，职责是保存分块本身。`chunk_fts` 是搜索索引，职责是帮助快速找到分块。

把它们分开是因为两者变化方式不同：

```text
原始分块：需要长期保存
搜索索引：可以删除、重建和更换实现
```

如果未来从 SQLite FTS5 换成 PostgreSQL、OpenSearch 或其他索引系统，应该只替换索引适配器，不动文档内容和业务模型。

当前 `replace_chunks()` 做了两件事：

```text
删除这个文档的旧分块
  -> 写入新的分块
  -> 删除这个文档的旧 FTS 索引
  -> 写入新的 FTS 索引
```

这保证同一份文档重新解析后不会出现旧内容和新内容混在搜索结果里。

## 6. 为什么 Level 2 先做全文检索

工程资料中经常出现标准号、设备型号、错误代码和精确参数，例如：

```text
GB/T xxxx
PLC-2000
Modbus TCP
220V
```

这类内容需要精确匹配。向量搜索更擅长理解“意思相近”，但不一定适合精确查型号和标准号。

中文还存在一个现实问题：SQLite FTS5 默认分词对中文连续文本并不理想。因此当前实现采用：

```text
先使用 FTS5
  -> 如果没有结果，再使用 LIKE
```

这不是最终的中文搜索方案，但足够用来验证“文档是否能找到、结果能否定位、过滤是否正确”。

## 7. 理想的 RAG 结构中，向量化应该放在哪里

完整的知识入库编排应该是：

```text
upload_document()
  -> create_document(pending)
  -> save_file()
  -> parse_document()
  -> clean_text()
  -> extract_metadata()
  -> split_into_chunks()
  -> save_chunks()
  -> generate_embeddings()
  -> save_vectors()
  -> build_keyword_index()
  -> mark_ready()
```

其中向量化明确放在：

```text
文本分块之后
全文索引和向量索引建立之前
```

代码职责应该是：

```text
DocumentService
  负责文档状态和入库总流程

ParserRegistry
  负责不同文件格式转成文本

Chunker
  负责文本分块

EmbeddingService
  负责把分块转换成向量

KeywordIndexer
  负责建立 FTS5 或其他全文索引

VectorRepository
  负责保存和查询向量
```

未来完整实现可以写成：

```python
def index_document(document_id: str) -> None:
    chunks = document_repository.get_chunks(document_id)
    keyword_indexer.index(chunks)
    vectors = embedding_service.embed([chunk.content for chunk in chunks])
    vector_repository.replace(document_id, vectors)
```

当前项目还没有 `EmbeddingService` 和 `VectorRepository`，所以不能说已经完成向量化。

## 8. 理想的用户问答核心编排

文档入库只是准备阶段。用户真正使用系统时，核心流程应该是：

```text
用户提出问题
  -> 保存问题
  -> 判断问题类型
  -> 提取行业、产品、地区和时间过滤条件
  -> 关键词检索
  -> 向量语义检索
  -> 合并候选结果
  -> 重排序
  -> 选出证据片段
  -> 构造带证据的提示词
  -> 调用 AI 模型
  -> 生成回答
  -> 附加文档、页码和章节引用
  -> 保存回答和引用
```

对应未来的服务结构：

```text
ChatService.answer()
  -> QuestionRouter.classify()
  -> QueryParser.extract_filters()
  -> SearchService.search()
  -> Reranker.rank()
  -> EvidenceSelector.select()
  -> PromptBuilder.build()
  -> LLMProvider.generate()
  -> CitationService.attach()
  -> ConversationRepository.save()
```

当前 Level 2 只完成了其中这一段：

```text
SearchService.search()
  -> 关键词检索
  -> 过滤
  -> 返回可引用的分块结果
```

## 9. 为什么现在还不能叫完整 RAG

RAG 的关键含义是“检索增强生成”：

```text
Retrieval：检索到相关资料
Augmented：把资料作为上下文提供给模型
Generation：模型根据上下文生成回答
```

当前代码已经有了第一部分的初版：

```text
Retrieval = FTS5 + LIKE 全文检索
```

但还没有：

```text
Augmented = 将检索结果构造成模型上下文
Generation = 调用模型生成带引用的回答
```

所以当前更准确的名称是：

> 具备文档预处理和全文检索能力的知识库基础工程。

## 10. 当前文件和完整主线的对应关系

```text
backend/app/api/documents.py
  文档进入系统的 HTTP 入口

backend/app/services/document_service.py
  文档入库编排

backend/app/adapters/parsers.py
  文件 -> 文本

backend/app/services/document_service.py
  文本 -> 分块

backend/app/adapters/sqlite_repository.py
  文档和分块持久化

backend/app/services/search_service.py
  查询 -> 检索结果

backend/app/api/search.py
  搜索功能的 HTTP 入口

backend/app/db.py
  数据库表和连接基础设施

backend/app/main.py
  启动时组装配置、数据库、文档服务和搜索服务
```

目前的组合根是 `main.py`，启动时大致完成：

```text
settings.ensure_directories()
  -> initialize_database()
  -> 组装 DocumentService
  -> 组装 SearchService
  -> 注册 API 路由
```

这就是当前代码已经具备的“基础业务编排”。完整的知识库核心编排还需要继续增加 `IndexingService`、`ChatService` 和 `CitationService`。

## 11. 下一阶段的自然顺序

后续不应跳过证据链直接做一个没有引用的聊天框。推荐顺序是：

```text
Level 3
  基于当前全文检索实现 AI 问答和引用

Level 4
  增加 EmbeddingService、向量索引和混合检索

Level 5
  增加实体、关系和知识图谱辅助检索

后续维护阶段
  增加反馈、引用评价、文档复核和重建索引
```

这样每一步都能单独运行和回溯，也能清楚知道系统距离完整 RAG 还差什么。

## 12. 本阶段验收

```text
cd backend
python -m pytest
```

结果：`4 passed`。

本阶段 Git 快照：

```text
d3aa871 feat: add level 2 full text search
```
