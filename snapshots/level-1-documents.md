# Level 1：文档导入闭环

状态：已完成

## 我这一阶段先解决什么问题

真正使用知识库的第一步不是问 AI，而是把一份资料可靠地放进去。这个动作如果没有状态和失败记录，用户会分不清“没导入”“正在处理”还是“解析失败”。所以这一阶段先把文档从上传到可检索片段的链路跑通。

## 文件为什么这样拆

- `domain/models.py`：描述文档和分块是什么，不依赖 FastAPI 或 SQLite；
- `api/documents.py`：只接收上传表单，避免 HTTP 细节污染业务；
- `services/document_service.py`：把一次导入串起来，是本阶段的核心编排；
- `adapters/file_store.py`：只处理文件复制和目录规则；
- `adapters/parsers.py`：只负责按扩展名读取文本，未来可增加 OCR；
- `adapters/sqlite_repository.py`：只负责把领域对象保存到 SQLite；
- `db.py`：仍只负责连接和表结构，不承载导入顺序。

## 函数如何配合

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

任何一步抛出异常都会进入 `failed` 状态。这样以后做“失败重试”时，只需要重新调用服务，不需要复制一套上传逻辑。

## 验收

```text
cd backend
python -m pytest
```

结果：4 passed。

## 当前限制

- 支持 TXT、Markdown 和文本型 PDF；
- 扫描型 PDF 尚未 OCR；
- 分块按固定字符数；
- 还没有全文检索和文档列表 API；
- 上传大小限制、重复文件哈希和更详细的错误表将在后续补充。
