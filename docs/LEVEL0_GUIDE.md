# Level 0 学习导读：我是如何拆分文件和函数的

这里记录的是可以复查和修改的设计过程，不是模型的隐性逐字思维链。

## 我是怎样一步步想到这些文件的

我先把自己放到实际使用场景里：你打开系统，想把一份白皮书放进去，之后还要按行业和关键词找到它，最后让 AI 根据它回答问题。这个场景看起来是“上传一个文件”，实际上至少包含路径配置、文件保存、文本解析、数据库记录和错误恢复几个不同问题。

如果把这些问题全塞进一个上传接口，最开始可能写得快，但以后 PDF 解析失败、换数据库或增加向量检索时，上传接口就会变成谁也不敢改的“大函数”。所以我先把它们按变化原因分开：配置会变、存储会变、解析器会变、业务状态会变，接口也会变。每一类变化都对应一个边界。

于是形成了这样的自然分工：`config.py` 管“应用应该去哪里找数据”，`db.py` 管“怎样可靠地打开和初始化数据库”，`router.py` 管“外部请求怎么进来”，`main.py` 管“启动时把这些东西按什么顺序接起来”。这不是为了文件数量好看，而是为了下次只改一个问题时，不必牵动全部代码。

Level 1 会把这个想法继续往前落地：上传接口不会自己解析文件，而是把任务交给 `DocumentService`；服务不会自己拼 SQL，而是交给 repository；解析器也不会写死在服务里，而是由 parser registry 选择。这样每个函数都能用一句话说明用途，也能单独测试。

## 先识别核心闭环

个人知识库最小闭环是：

```text
启动应用 -> 准备存储 -> 保存文档元数据 -> 检索文档 -> 生成带依据的回答
```

Level 0 只完成前两步和后续步骤的接口边界。原因是如果目录、配置、数据库连接和启动顺序没有稳定下来，后面的上传和问答会把路径、连接和错误处理重复写在多个地方。

## 决策点一：为什么有 config.py

如果每个文件都直接写 `data/knowledge_base.sqlite3`，将来测试、迁移数据库或更换存储时会同时修改很多文件。因此由 `Settings` 统一提供路径和运行参数。`ensure_directories()` 是启动前的唯一目录准备动作。

## 决策点二：为什么有 db.py

文档、分块、对话和实体都需要持久化。`db.py` 先提供三个最小能力：

- `connect()`：建立规范化连接；
- `initialize_database()`：幂等建表；
- `database_is_initialized()`：给健康检查使用。

它暂时不包含文档业务 SQL，因为“数据库连接规则”和“文档生命周期规则”应该分开。Level 1 会增加 repository/service，而不是继续把所有逻辑塞进 `db.py`。

## 决策点三：为什么有 router.py

路由是外部请求的入口，不应该负责解析 PDF、切分文本或调用模型。当前只提供健康检查和模块列表，用于验证服务可用以及前后端导航契约。后续路由会调用 service，例如：

```python
@router.post("/documents")
def upload_document(command: UploadDocumentCommand):
    return document_service.import_document(command)
```

## 决策点四：为什么 main.py 只有少量代码

`main.py` 是组合根（composition root）：负责把配置、数据库、路由和未来服务组装起来。它不应该变成“所有功能都写在这里”的巨型文件。`lifespan()` 体现启动顺序，后续会继续扩展为：

```text
配置
  -> 目录
  -> 数据库
  -> 文档解析器注册表
  -> 检索器注册表
  -> AI Provider
  -> API
```

## 决策点五：为什么预留 enabled 模块

页面未来会增加图谱、阅读计划、方案对比等功能。如果导航、页面、接口全部硬编码在一个组件中，扩展时容易互相影响。因此 Level 0 先建立模块契约：`key`、`label`、`route`、`enabled`。当前未实现功能明确关闭，未来启用时只增加对应模块。

## 下一阶段如何接上

Level 1 的核心编排应是：

```text
API upload
  -> DocumentService.create_pending()
  -> FileStore.save()
  -> ParserRegistry.parse()
  -> Chunker.split()
  -> DocumentRepository.save_chunks()
  -> DocumentService.mark_ready()
```

每一步都可以单独测试；任何一步失败都把文档标记为 `failed`，保留错误信息并允许重试。这比在一个 API 函数中顺序写几十行逻辑更适合长期维护。
