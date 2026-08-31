# Level 2：全文检索

状态：已完成

## 这一阶段解决什么

Level 1 已经把资料切成分块，但如果不能找到这些分块，知识库仍然只是文件仓库。这一阶段先实现可靠的关键词检索，尤其照顾标准号、产品型号、行业术语和中文连续词。

## 我是怎样考虑拆分的

搜索请求会不断变化，数据库实现也可能从 SQLite 换成 PostgreSQL 或 OpenSearch，所以 API 不直接写 SQL。`SearchService` 先接收一个问题和过滤条件，再交给 repository 找候选，最后统一过滤结果和返回引用。

`document_chunks` 是知识正文的结构化副本；`chunk_fts` 是为搜索建立的索引副本。把二者分开，是因为索引可以删除后重建，不应该影响原始分块。文档重新解析时，repository 会先替换旧分块，再同步该文档的 FTS 记录。

## 核心编排

```text
GET /api/search
  -> SearchService.search()
  -> repository.search_chunks()
  -> FTS5 MATCH
  -> 中文/特殊术语 LIKE 保底
  -> SearchService._apply_filters()
  -> 返回文档、分块、顺序和定位信息
```

## 验收

```text
cd backend
python -m pytest
```

测试覆盖文档导入后建立 FTS 索引，并按行业过滤返回正确分块。

## 为什么这一阶段不做向量化

向量检索需要选择 embedding 模型、向量维度和索引实现，还会涉及本地模型或外部服务的数据边界。先用全文检索把“导入 → 找到原文”闭环跑通，可以先验证数据结构和引用设计，再在 Level 4 增加语义检索。

## 当前限制

- FTS5 对中文分词能力有限，因此加入 LIKE 保底；
- 暂未做结果高亮；
- 暂未接入向量检索和重排序；
- 搜索结果上限为 50 个分块。
