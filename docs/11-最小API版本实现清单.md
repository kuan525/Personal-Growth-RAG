# 最小 API 版本实现清单

## 1. 目标

第一版不做完整个人图谱、memory、decision support、TUI、agent 接入，也不做复杂 incremental update。

第一版只证明一件事：

> 用户可以通过 API 上传文档、查看文档状态、基于已上传文档提问，并获得带 citation 的回答。

也就是最小闭环：

```text
upload document
  -> parse
  -> chunk
  -> embed
  -> index
  -> ask question
  -> retrieve chunks
  -> answer with citations
  -> inspect document status
```

## 2. 第一版必须实现的三个接口

### 2.1 上传文档

```http
POST /documents
```

职责：

- 接收 PDF / Markdown / TXT 文件
- 创建 document record
- 计算 content_hash
- 解析文本
- 生成 chunks
- 生成 embeddings
- 写入 vector index
- 写入 metadata store
- 返回 document_id、status、chunk_count

### 2.2 查看文档状态

```http
GET /documents
GET /documents/{document_id}
```

职责：

- 查看已上传 documents
- 查看单个 document 的处理状态
- 查看 chunk_count
- 查看失败原因
- 后续 incremental update 也依赖这个状态模型

### 2.3 问问题

```http
POST /questions
```

职责：

- 接收 query_text
- 生成 query embedding
- 从 vector index 检索 chunks
- 组装 context
- 调用 LLM 生成 answer
- 返回 answer 和 citations
- 记录 query trace

## 3. 第一版推荐技术栈

### 3.1 API 框架

推荐：

```text
FastAPI
Pydantic v2
Uvicorn
```

理由：

- Python RAG 生态最顺
- API 开发快
- Pydantic 适合定义 request / response schema
- 后续可被 Rust TUI、TypeScript agent layer 或 Web UI 调用

### 3.2 数据库

推荐：

```text
SQLite
SQLAlchemy
```

理由：

- 本地优先
- 足够支撑 metadata、query log、citation、eval
- 后续迁移成本低

第一版可以不引入复杂 migration，但 schema 要清晰。

### 3.3 Vector Index

推荐第一版：

```text
FAISS
```

理由：

- 快速跑通 MVP
- 本地使用简单
- 适合第一阶段 baseline

注意：

- FAISS 本身不擅长 delete / update
- Phase 4 incremental update 时再切 Qdrant 更合理

### 3.4 文档解析

推荐：

```text
TXT: pathlib read_text
Markdown: markdown-it-py 或直接按文本处理
PDF: PyMuPDF
```

第一版目标是抽取可用文本，不追求复杂 layout parsing。

### 3.5 Embedding

第一版统一使用 **OpenRouter** 作为 embedding provider。

要求：

- 通过 provider interface 调用，不把 HTTP 细节散落到业务代码
- embedding model 名称通过 config 注入
- chunk embedding 和 query embedding 共用同一套 provider 封装

### 3.6 LLM

第一版统一使用 **OpenRouter** 作为 answer model provider。

要求：

- 通过 provider interface 调用，不把具体模型写死在业务代码里
- chat model 名称通过 config 注入
- 输入 query + retrieved context
- 输出 answer
- evidence 不足时允许拒答

### 3.7 OpenRouter 配置

第一版约定使用 OpenAI-compatible 接口格式接入 OpenRouter。

最小配置：

```text
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=sk-or-v1-demo-placeholder
OPENROUTER_EMBEDDING_MODEL=your-embedding-model
OPENROUTER_CHAT_MODEL=your-chat-model
```

接口约定：

- embedding 走 `/embeddings`
- answer generation 走 `/chat/completions`

注意：

- key 先用占位值，后续再替换成真实值
- 代码里不要写死 key
- provider 层要把 embedding 和 LLM 调用分开封装

## 4. 最小项目结构

第一版建议目录：

```text
src/
  app/
    main.py
    config.py
    api/
      documents.py
      questions.py
    schemas/
      documents.py
      questions.py
    storage/
      database.py
      models.py
      repositories.py
    ingestion/
      service.py
      parsers.py
    chunking/
      splitter.py
    embeddings/
      service.py
    indexing/
      faiss_index.py
    retrieval/
      service.py
    answering/
      service.py
      prompts.py
    common/
      ids.py
      time.py

data/
  sources/
  indexes/
  app.db

tests/
```

说明：

- `api/` 只处理 HTTP。
- `schemas/` 定义 request / response。
- `storage/` 管 SQLite metadata。
- `ingestion/` 管文档进入系统。
- `chunking/` 管 chunk 切分。
- `embeddings/` 管 embedding 生成。
- `indexing/` 管 FAISS index。
- `retrieval/` 管 query -> chunks。
- `answering/` 管 context -> answer。

## 5. 第一版必须实现的数据表

### 5.1 documents

必须字段：

```text
document_id
source_name
source_type
file_type
file_size
content_hash
status
chunk_count
error_message
created_at
updated_at
ingested_at
```

status：

```text
processing
active
failed
deleted
```

第一版可以先不做 `modified` 和 `superseded`，但字段设计要允许后续扩展。

### 5.2 chunks

必须字段：

```text
chunk_id
document_id
chunk_order
chunk_text
chunk_hash
source_name
page_start
page_end
heading_path
status
created_at
```

status：

```text
active
deleted
```

### 5.3 embeddings

必须字段：

```text
embedding_id
chunk_id
index_position
model_name
vector_dim
created_at
```

说明：

- FAISS 只知道向量位置。
- 必须用 metadata 映射 `index_position -> chunk_id`。

### 5.4 query_runs

必须字段：

```text
query_id
query_text
created_at
```

### 5.5 retrieval_results

必须字段：

```text
retrieval_id
query_id
chunk_id
score
rank
final_selected
created_at
```

### 5.6 answers

必须字段：

```text
answer_id
query_id
answer_text
whether_refused
created_at
```

### 5.7 citations

必须字段：

```text
citation_id
answer_id
chunk_id
source_name
quote_text
created_at
```

## 6. API 契约

## 6.1 POST /documents

### Request

```http
multipart/form-data
file: PDF / Markdown / TXT
source_type: document | project_note | review | decision_log | manual_note
```

### Response

```json
{
  "document_id": "doc_...",
  "source_name": "README.md",
  "file_type": "md",
  "status": "active",
  "chunk_count": 12,
  "content_hash": "...",
  "error_message": null
}
```

### 失败 Response

```json
{
  "document_id": "doc_...",
  "source_name": "bad.pdf",
  "status": "failed",
  "chunk_count": 0,
  "error_message": "PDF parse failed"
}
```

## 6.2 GET /documents

### Response

```json
{
  "documents": [
    {
      "document_id": "doc_...",
      "source_name": "README.md",
      "source_type": "document",
      "file_type": "md",
      "status": "active",
      "chunk_count": 12,
      "created_at": "...",
      "ingested_at": "..."
    }
  ]
}
```

## 6.3 GET /documents/{document_id}

### Response

```json
{
  "document_id": "doc_...",
  "source_name": "README.md",
  "source_type": "document",
  "file_type": "md",
  "status": "active",
  "chunk_count": 12,
  "content_hash": "...",
  "error_message": null,
  "created_at": "...",
  "updated_at": "...",
  "ingested_at": "..."
}
```

## 6.4 POST /questions

### Request

```json
{
  "query_text": "这个项目为什么不建议一开始用 Rust + TypeScript？",
  "top_k": 5
}
```

### Response

```json
{
  "query_id": "query_...",
  "answer_id": "ans_...",
  "answer": "...",
  "whether_refused": false,
  "citations": [
    {
      "chunk_id": "chunk_...",
      "document_id": "doc_...",
      "source_name": "README.md",
      "quote_text": "..."
    }
  ]
}
```

## 7. 必须实现的核心流程

## 7.1 Document Ingestion Flow

```text
receive file
  -> validate extension
  -> save or read file content
  -> compute content_hash
  -> create document(status=processing)
  -> parse text
  -> split chunks
  -> insert chunks
  -> generate embeddings
  -> add vectors to FAISS
  -> insert embedding metadata
  -> update document(status=active, chunk_count=n)
```

失败时：

```text
update document(status=failed, error_message=...)
```

## 7.2 Question Answering Flow

```text
receive query
  -> create query_run
  -> embed query
  -> search FAISS top_k
  -> map index_position to chunk_id
  -> load chunks
  -> record retrieval_results
  -> build context
  -> call LLM
  -> create answer
  -> create citations
  -> return response
```

## 8. 第一版可以暂时不做的内容

明确不做：

- user auth
- streaming response
- async background job
- graph
- memory
- decision support
- rerank
- BM25
- Qdrant
- Web UI
- TUI
- agent integration
- document delete/update
- complex PDF layout parsing
- OCR

这些不是放弃，而是后续 phase。

## 9. 第一版必须保留的扩展点

虽然不实现复杂能力，但必须预留：

- `source_type`
- `content_hash`
- `document.status`
- `chunk.status`
- `query_runs`
- `retrieval_results`
- `citations`
- embedding provider interface
- LLM provider interface

这些是后续 incremental update、evaluation、graph、memory、decision support 的地基。

## 10. 最小验收标准

第一版通过标准：

- [ ] `POST /documents` 可以上传 PDF / Markdown / TXT
- [ ] 上传后 document status 变成 `active`
- [ ] chunks 被写入数据库
- [ ] embeddings 被生成
- [ ] FAISS index 可被 query
- [ ] `GET /documents` 能看到文档列表
- [ ] `GET /documents/{document_id}` 能看到状态和 chunk_count
- [ ] `POST /questions` 能返回 answer
- [ ] answer 至少包含一个 citation
- [ ] query_run、retrieval_results、answer、citations 都被记录
- [ ] 解析失败时 document status 为 `failed` 且有 error_message

## 11. 最小测试用例

### Test 1：上传 Markdown

- 输入：README.md
- 预期：status=active，chunk_count > 0

### Test 2：上传 TXT

- 输入：sample.txt
- 预期：status=active，chunk_count > 0

### Test 3：上传 PDF

- 输入：sample.pdf
- 预期：status=active 或 failed with clear error_message

### Test 4：查看文档列表

- 调用：GET /documents
- 预期：返回已上传文档

### Test 5：问已知问题

- 调用：POST /questions
- 预期：answer 与 citation 返回，citation 指向正确 source_name

### Test 6：问无依据问题

- 调用：POST /questions
- 预期：answer 应说明资料不足或不确定

## 12. 实现顺序

推荐按这个顺序写代码：

1. 创建项目结构。
2. 定义 config。
3. 定义 SQLAlchemy models。
4. 初始化 SQLite。
5. 实现 document repository。
6. 实现 parsers。
7. 实现 chunk splitter。
8. 实现 embedding service。
9. 实现 FAISS index service。
10. 实现 ingestion service。
11. 实现 `POST /documents`。
12. 实现 `GET /documents` 和 `GET /documents/{id}`。
13. 实现 retrieval service。
14. 实现 answer service。
15. 实现 `POST /questions`。
16. 写最小测试。

## 13. 第一版的关键判断

第一版最重要的不是回答质量有多高，而是：

- metadata 是否稳定
- document -> chunk -> embedding -> retrieval -> answer -> citation 链路是否打通
- 失败是否可见
- query trace 是否可追溯

只要这四点成立，后续 retrieval、rerank、incremental update、graph、memory、decision support 才有可靠地基。
