# 个人 FDE 知识库项目设计文档

版本：0.1.0（设计基线）  
定位：单用户、本地优先、可逐步扩展的行业知识问答工具

## 1. 项目目标

系统帮助个人 FDE 工程师把行业方案、白皮书、介绍材料和个人笔记沉淀为可检索知识，并通过 AI 快速完成：

- 理解一个行业的基本概念、参与方、业务流程和技术栈；
- 根据多份资料比较方案、产品、限制条件和实施风险；
- 从原文中定位依据，避免只得到没有出处的模型生成内容；
- 把学习内容逐步转化为项目背景、需求、方案和复盘笔记。

“可扩展”指模块和页面可以增加，不指第一版就部署复杂基础设施。

## 2. 明确边界

本版本只服务一个用户。以下内容不进入本轮计划：

- 企业化部署、高可用、租户隔离；
- 多用户、权限协作、交流社区；
- 联网搜索、GitHub 自动导入；
- 自动化严格备份编排；
- 面向生产交付的自动决策。

数据量按个人资料库设计，原始资料预计不超过 500GB。备份由用户手动执行；应用只提供导出和恢复所需的清晰目录结构，不自动接管备份策略。

## 3. 技术基线

推荐个人长期方案 A 的轻量实现：

```text
前端：Vue 3（沿用现有工作区熟悉的前端方向）
后端：Python + FastAPI
数据库：SQLite 起步，数据量和并发增加后迁移 PostgreSQL + pgvector
文件：本地 data/documents 目录
全文检索：SQLite FTS5
语义检索：第一阶段预留接口；第二阶段接入本地向量索引
AI：Provider 接口，支持本地模型或兼容 OpenAI API 的模型
运行：本地 Python 进程；成熟后再增加 Docker Compose
```

选择 SQLite 起步，是因为单用户、单机和 500GB 原始文件的核心瓶颈在文件存储与解析，而不是事务数据库。原始文件不应直接塞入数据库；数据库只保存元数据、解析文本、索引和问答记录。

未来升级路径：

```text
SQLite + FTS5
  -> PostgreSQL + pgvector
  -> 可选 Qdrant（大量向量时）
  -> 可选 Neo4j（图关系成为主要查询时）
```

所有检索和 AI 服务都通过接口隔离，升级存储引擎不应改变页面和业务用例。

## 4. 领域模型

### 4.1 文档元数据

保留字段如下，删除不必要的商业管理字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | UUID | 文档唯一标识 |
| `title` | string | 文档标题 |
| `document_type` | enum | 方案、白皮书、介绍、标准摘要、笔记、案例等 |
| `industry` | string | 所属行业，可多选或层级化 |
| `author` | string | 作者或编写组织，合并原“来源组织” |
| `published_at` | date | 发布日期，可为空 |
| `expires_at` | date | 有明确有效期时填写，可为空 |
| `language` | string | 中文、英文等 |
| `trust_level` | enum | `high`、`medium`、`low` |
| `region` | string | 适用地区，可为空 |
| `project_stage` | enum | 学习、调研、方案、实施、复盘 |
| `keywords` | JSON | 关键词数组 |
| `related_products` | JSON | 相关产品或技术数组 |
| `version` | string | 文档版本，可为空 |
| `reviewed_at` | datetime | 最后一次人工复核时间，可为空 |
| `created_at` / `updated_at` | datetime | 系统时间 |

不设置“版权状态”和“原始文件”业务字段。个人文件保存位置由系统内部管理；版权提示可作为界面说明，不进入核心数据模型。

### 4.2 核心实体

```text
Document       文档
DocumentChunk  文档分块
Tag            标签
Entity         行业实体
Relation       实体关系
Conversation   对话
Message        消息
Citation       回答引用
Note           个人笔记
```

每个 `DocumentChunk` 必须保留章节、页码或原文位置，使回答可以引用到具体依据。

## 5. 页面结构与可插拔导航

页面采用“固定壳层 + 功能模块注册表”。左侧导航只展示已启用模块，路由预留但不提前实现复杂功能。

```text
/                         工作台
/documents                文档库
/documents/:id            文档详情、原文定位、分块
/search                   全局检索
/chat                     AI 问答
/chat/:conversation_id   对话详情
/notes                    个人笔记
/graph                    知识图谱（预留）
/projects                项目空间（第二阶段）
/settings                模型、存储、索引和安全设置
/about                    系统状态、版本和设计决策
```

模块注册接口示例：

```python
# frontend/src/modules/registry.py（概念位置，前端实现可用 TS）
class ModuleDefinition:
    key: str
    label: str
    route: str
    icon: str
    enabled: bool
    order: int

def get_enabled_modules(settings) -> list[ModuleDefinition]: ...
```

新增知识图谱、阅读计划或方案对比时，只增加模块、路由和 API，不重写主布局。

## 6. 后端目录和 Python 函数编排

推荐目录：

```text
app/
├── main.py                 # 创建 FastAPI 应用和生命周期
├── config.py               # 环境变量与路径配置
├── api/
│   ├── router.py            # 汇总路由
│   ├── documents.py        # 文档 API
│   ├── search.py           # 检索 API
│   ├── chat.py             # 问答 API
│   └── schemas.py           # 请求/响应模型
├── domain/
│   ├── models.py            # 领域数据类
│   └── enums.py             # 文档类型、阶段、可信等级
├── services/
│   ├── document_service.py  # 文档生命周期
│   ├── ingest_service.py    # 导入编排
│   ├── search_service.py    # 混合检索
│   ├── chat_service.py      # RAG 问答
│   └── note_service.py      # 笔记
├── ports/
│   ├── repository.py        # 数据仓储接口
│   ├── parser.py            # 文档解析接口
│   ├── retriever.py         # 检索接口
│   └── llm.py               # 模型接口
├── adapters/
│   ├── sqlite_repository.py
│   ├── local_file_store.py
│   ├── fts_retriever.py
│   ├── vector_retriever.py  # 第二阶段
│   └── llm_provider.py
└── tests/
```

### 6.1 文档导入流程

```python
# services/ingest_service.py
def import_document(file_path, metadata) -> Document:
    file_id = document_service.create_pending(metadata)
    raw = file_store.save(file_path, file_id)
    parsed = parser_registry.parse(raw)
    chunks = chunker.split(parsed)
    document_service.replace_chunks(file_id, chunks)
    index_service.index_text(file_id, chunks)
    document_service.mark_ready(file_id)
    return document_service.get(file_id)
```

必须支持失败状态：`pending`、`processing`、`ready`、`failed`。解析失败时保留原文件和错误信息，允许重新处理。

### 6.2 检索流程

```python
# services/search_service.py
def search(query: str, filters: SearchFilters) -> SearchResult:
    normalized = query_parser.normalize(query)
    keyword_hits = fts_retriever.search(normalized, filters)
    vector_hits = vector_retriever.search(normalized, filters)  # 未启用时返回空集
    merged = ranker.merge(keyword_hits, vector_hits)
    return citation_builder.attach_locations(merged)
```

第一阶段只实现 `fts_retriever`，但保留 `vector_retriever` 端口，避免未来修改 API。

### 6.3 AI 问答流程

```python
# services/chat_service.py
def answer(conversation_id: str, question: str) -> Answer:
    intent = question_router.classify(question)
    filters = query_parser.extract_filters(question, intent)
    evidence = search_service.search(question, filters)
    if evidence.is_empty():
        return answer_builder.insufficient_evidence(question)
    prompt = prompt_builder.build(question, evidence, intent)
    draft = llm.generate(prompt)
    answer = answer_builder.with_citations(draft, evidence)
    conversation_store.append(conversation_id, question, answer)
    return answer
```

回答规则：没有检索证据时明确说“资料库中没有足够依据”；回答中区分原文结论、跨文档归纳和推测；每个关键结论附文档与页码/章节。

## 7. 分级实现计划

### Level 0：工程骨架

目标：项目可运行、可测试、可追踪。

- 初始化 Python 包和前端包；
- 配置 `data/`、`storage/`、`logs/` 路径；
- 建立 FastAPI 健康检查；
- 建立前端布局和可插拔导航；
- 建立 SQLite 数据库初始化；
- 加入 `.gitignore` 和开发说明。

验收：启动服务后可打开工作台，`GET /health` 返回正常，空数据库可初始化。

### Level 1：文档最小闭环

- 文档上传；
- 文件哈希和重复判断；
- 元数据录入；
- 文本解析；
- 分块和页码记录；
- 文档列表、详情、删除；
- 失败重试。

验收：导入 PDF 后能看到标题、类型、行业、作者、页码和解析状态。

### Level 2：全文检索

- SQLite FTS5；
- 标题、正文、关键词检索；
- 行业、文档类型、阶段和可信等级过滤；
- 结果高亮；
- 从结果跳转到文档位置。

验收：用标准号、产品型号和自然语言分别检索，结果可定位到原文。

### Level 3：基础 AI 问答

- LLM Provider 抽象；
- 选择检索范围；
- 基于 FTS 结果生成答案；
- 引用文档和页码；
- 保存对话；
- “有帮助/不准确”反馈。

验收：回答不会在无证据时假装确定，并能打开引用位置。

### Level 4：语义检索

- 接入 embedding provider；
- 本地向量索引或 PostgreSQL/pgvector；
- 关键词 + 向量融合排序；
- embedding 模型可配置；
- 重建索引命令。

验收：同义表达和自然语言问题的召回率明显高于纯关键词检索。

### Level 5：知识图谱预留实现

- 实体和关系数据表；
- 从文档分块提取候选实体；
- 人工确认后入图；
- 图谱页面；
- 图谱结果参与问答检索。

验收：可以从一个方案追到适用行业、产品、技术和依据文档。

## 8. 数据不泄露措施

- 默认只监听本机地址，不开放局域网端口；
- 原始文件、解析文本和数据库默认保存在项目数据目录；
- 云端模型调用设置为可关闭；
- 对话发送前显示将要发送的上下文范围；
- 提供“仅本地模型”模式；
- 日志不记录完整文档正文和完整客户资料；
- 对外部模型使用环境变量配置密钥，不写入 Git；
- 删除操作先标记删除，确认后再清理文件；
- 提供手动导出：数据库、原始文件、配置说明分别导出。

个人使用不需要复杂权限系统，但“本地默认、外发可见、模型可切换”应从第一版设计进去。

## 9. 手动备份和恢复

不做自动备份调度。提供两个命令即可：

```text
python -m app.cli export --output <目录>
python -m app.cli restore --input <目录>
```

导出目录建议：

```text
export/
├── database.sqlite
├── documents/
├── manifest.json
└── README.txt
```

`manifest.json` 记录导出时间、文件数量、文件哈希和应用版本。恢复前先在临时目录校验清单，恢复失败不得覆盖当前数据。

## 10. Git 快照规范

每完成一个 Level 建立一个可回溯提交：

```text
level-0-foundation   项目骨架
level-1-documents    文档导入闭环
level-2-search       全文检索
level-3-chat         基础问答
level-4-semantic     语义检索
level-5-graph        知识图谱
```

每次快照提交信息应包含：完成内容、验证命令、已知限制。`snapshots/` 目录只保存阶段说明和验收记录，不复制整个代码工程。

## 11. 第一阶段当前任务清单

本设计文档完成后，下一次编码只做 Level 0：

1. 创建 `app/`、`frontend/`、`tests/` 基础目录；
2. 编写配置、健康检查和 SQLite 初始化；
3. 建立文档领域模型和仓储接口；
4. 创建前端固定布局、工作台、文档库和问答占位路由；
5. 加入最小测试；
6. 建立 `level-0-foundation` Git 快照。

不在 Level 0 提前实现图谱、向量数据库、联网功能或多用户能力。
