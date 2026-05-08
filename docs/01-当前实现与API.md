# 当前实现与 API

## 已实现

### Documents

- 支持 `.txt` / `.md` / `.pdf` 上传。
- 原文件保存到 `data/uploads/`。
- 支持本地目录批量导入。
- `.txt` / `.md` 使用 UTF-8 文本读取。
- `.pdf` 使用 `pdfminer.six` 提取文本。

### Chunks

- 使用 `RecursiveCharacterTextSplitter` 做基础切分。
- 默认 `chunk_size=200`，`chunk_overlap=30`。
- chunk JSON 调试文件保存到 `data/chunks/`。

### SQLite Metadata

- SQLite 文件：`data/app.db`。
- 使用 SQLAlchemy 定义和读写表。
- 当前表：`documents`、`chunks`、`embeddings`。
- 服务启动时自动创建表。

### Retrieval & QA

- 使用 DashScope `text-embedding-v4` 生成 1024 维向量。
- 使用 FAISS `IndexFlatIP` 做本地向量检索。
- 向量索引保存到 `data/indexes/chunks.faiss`。
- 支持 `/v1/search` 返回 relevant chunks。
- 支持 `/v1/questions` 调用 DeepSeek V4 Pro 生成 answer with citations。


## 当前入口

```bash
uvicorn personal_growth_rag.main:app --reload
python -m personal_growth_rag.cli.ingest_dir data/library
```

所有公开 HTTP API 都使用 `/v1` 前缀；旧的无版本路径不再保留。

## API

### Health Check

```http
GET /v1/health
```

返回：

```json
{
  "success": true,
  "error_code": null,
  "message": "ok",
  "data": {"status": "ok"},
  "request_id": null
}
```

### 上传文档

```http
POST /v1/documents
Content-Type: multipart/form-data
```

响应核心字段在 `data` 内：

```json
{
  "success": true,
  "error_code": null,
  "message": "ok",
  "data": {
    "document_id": "doc_xxx",
    "source_name": "document.pdf",
    "file_type": "pdf",
    "status": "active",
    "chunk_count": 8
  },
  "request_id": null
}
```

成功响应只暴露前端需要的文档公开字段；`stored_path`、`chunk_path`、`error_message` 保留在数据库中用于本地排障，不放进成功态 API data。

### 查询文档列表

```http
GET /v1/documents
```

返回文档摘要列表，不返回 chunk 内容，也不返回本地存储路径。

### 查询文档详情

```http
GET /v1/documents/{document_id}
```

成功时返回文档公开字段；找不到时返回统一错误响应和 `404`。

### 语义检索

```http
POST /v1/search
Content-Type: application/json
```

请求：

```json
{"query_text":"我有哪些后端开发经历？","top_k":5}
```

返回：

```json
{
  "success": true,
  "error_code": null,
  "message": "ok",
  "data": {
    "results": [
    {
      "document_id": "doc_xxx",
      "source_name": "resume.pdf",
      "chunk_id": "chk_xxx",
      "chunk_order": 3,
      "score": 0.81,
      "text": "..."
    }
    ]
  },
  "request_id": null
}
```

### RAG 问答

```http
POST /v1/questions
Content-Type: application/json
```

请求：

```json
{"question":"我有哪些后端开发经历？","top_k":5}
```

返回：

```json
{
  "success": true,
  "error_code": null,
  "message": "ok",
  "data": {
    "answer": "...",
    "citations": [
    {
      "document_id": "doc_xxx",
      "source_name": "resume.pdf",
      "chunk_id": "chk_xxx",
      "chunk_order": 3,
      "score": 0.81,
      "text": "..."
    }
    ]
  },
  "request_id": null
}
```

### 统一响应

所有 API 都返回同一层 envelope。成功时 `success=true`、`error_code=null`、业务数据在 `data`；失败时 `success=false`、`data=null`、错误信息在 `error_code/message`。

```json
{
  "success": false,
  "error_code": "DOCUMENT_NOT_FOUND",
  "message": "Document not found",
  "data": null,
  "request_id": null
}
```
