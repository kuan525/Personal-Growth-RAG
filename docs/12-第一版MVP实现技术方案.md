# 第一版 MVP 实现技术方案

## 1. 目标边界

第一版 MVP 只实现一个 local-first 的 API 服务，目标是打通 `document -> parse -> chunk -> embedding -> FAISS -> retrieval -> answer -> citation` 的最小闭环。

本阶段只做三类能力：

1. 上传文档：`POST /documents`
2. 查看文档状态：`GET /documents`、`GET /documents/{document_id}`
3. 基于已上传文档问问题：`POST /questions`

本阶段不做 graph、memory、decision support、BM25、rerank、Qdrant、TUI、Web UI、agent integration。

## 2. 技术栈

- Python 3.11+
- FastAPI：API 服务
- Pydantic v2：配置与接口 schema
- SQLAlchemy：关系型数据记录
- SQLite：本地 MVP 数据库
- FAISS：本地向量索引
- OpenRouter：统一接入 embedding 与 chat model
- PyMuPDF：PDF 解析

## 3. 模块职责

```text
src/app/main.py                 FastAPI app 入口
src/app/api/                    API route
src/app/schemas/                请求与响应 schema
src/app/storage/                SQLAlchemy model、session、repository
src/app/ingestion/              文件落盘、parse、chunk、embedding、index 写入
src/app/chunking/               文本切分
src/app/providers/              OpenRouter provider 抽象与实现
src/app/embeddings/             embedding service
src/app/indexing/               FAISS index wrapper
src/app/retrieval/              query embedding、FAISS search、retrieval trace
src/app/answering/              prompt 组装、LLM 回答、citation 写入
src/app/common/                 id、time、hash、enum、exception
```

## 4. API 契约

### 4.1 上传文档

```http
POST /documents
Content-Type: multipart/form-data
```

字段：

- `file`: 上传文件

支持文件：

- `.txt`
- `.md` / `.markdown`
- `.pdf`

响应核心字段：

- `document_id`
- `source_name`
- `source_type`
- `file_type`
- `file_size`
- `content_hash`
- `status`
- `chunk_count`
- `error_message`
- `parser_type`
- `storage_path`
- `created_at`
- `updated_at`
- `ingested_at`

### 4.2 查看文档列表

```http
GET /documents
```

返回所有 document 的状态与 metadata。

### 4.3 查看单个文档

```http
GET /documents/{document_id}
```

用于检查单个文档的 `status`、`chunk_count`、`content_hash`、`error_message`。

### 4.4 问问题

```http
POST /questions
Content-Type: application/json
```

请求：

```json
{
  "query_text": "这个系统第一版用什么技术栈？",
  "top_k": 5
}
```

响应核心字段：

- `query_id`
- `answer_id`
- `answer_text`
- `whether_refused`
- `confidence_label`
- `citations`
- `created_at`

## 5. 数据表

MVP 使用 7 张表保留最小 trace：

1. `documents`：文档级 metadata、状态、hash、parser、存储路径
2. `chunks`：chunk 文本、顺序、hash、来源信息
3. `embeddings`：chunk 到 FAISS `index_position` 的持久映射
4. `query_runs`：每次问题请求
5. `retrieval_results`：每次检索结果与排序
6. `answers`：LLM 回答与拒答状态
7. `citations`：answer 到 chunk 的引用证据

关键约束：

- `documents.content_hash` 为 incremental update 预留。
- `chunks.chunk_order` 保证文档内顺序可追踪。
- `embeddings.index_position` 是 FAISS 结果回查 chunk 的稳定桥梁。
- `query_runs -> retrieval_results -> answers -> citations` 必须完整落库，便于后续调试 retrieval 和 citation。

## 6. 请求流

### 6.1 文档上传流

1. API 接收上传文件。
2. 计算 `content_hash`。
3. 创建 `document(status=processing)`。
4. 文件落盘到 `SOURCE_DIR`。
5. parser 解析文本。
6. splitter 切分 chunk。
7. OpenRouter 生成 chunk embeddings。
8. embeddings 表写入 `index_position`。
9. FAISS 写入向量。
10. 更新 `document(status=active, chunk_count=n)`。

失败时：

1. rollback 当前未完成写入。
2. 更新 document 为 `failed`。
3. 写入 `error_message`。

### 6.2 问答流

1. API 接收 `query_text`。
2. 创建 `query_run`。
3. OpenRouter 生成 query embedding。
4. FAISS search top_k。
5. 通过 `embeddings.index_position` 找回 `chunk_id`。
6. 读取 chunk 文本。
7. 写入 `retrieval_results`。
8. 组装 context prompt。
9. OpenRouter chat 生成 answer。
10. 写入 `answers`。
11. 写入 `citations`。
12. 返回 answer 与 citations。

如果没有检索结果，系统返回 `whether_refused=true` 和 `confidence_label=insufficient_evidence`。

## 7. OpenRouter provider 约束

OpenRouter 调用只能出现在 `providers/openrouter.py`。

业务层只能依赖：

- `EmbeddingProvider.embed_texts(texts)`
- `ChatProvider.chat_answer(system_prompt, user_prompt)`

模型名、base url、API key 都通过配置注入，不允许在 ingestion、retrieval、answering 里直接拼 OpenRouter URL。

## 8. 本地运行

准备环境变量：

```bash
cp .env.example .env
```

编辑 `.env`，填入：

```env
OPENROUTER_API_KEY=你的 OpenRouter key
OPENROUTER_EMBEDDING_MODEL=你的 embedding model
OPENROUTER_CHAT_MODEL=你的 chat model
```

安装依赖：

```bash
pip install -e ".[dev]"
```

启动服务：

```bash
uvicorn src.app.main:app --reload
```

健康检查：

```bash
curl http://localhost:8000/health
```

## 9. 测试

运行：

```bash
pytest
```

当前测试覆盖：

- Markdown 上传
- TXT 上传
- 空文件拒绝
- 文档列表
- 文档详情
- 已有文档下问答返回 answer + citation
- 无文档下问答返回资料不足

测试使用 fake provider，不调用真实 OpenRouter。

## 10. 后续扩展顺序

完成 MVP 后，再按以下顺序扩展：

1. 增量更新：基于 `content_hash` 和 document status 做重复检测、更新、删除。
2. retrieval quality：加入 BM25、rerank、evaluation set。
3. graph：基于 source/chunk/heading/entity/relation 扩展个人图谱。
4. memory：将长期偏好、复盘、阶段变化沉淀为可检索 memory。
5. decision support：围绕时间节点、实践节点输出建议与 evidence trace。
6. TUI / agent integration：在 API 稳定后再接 Rust TUI 或 TypeScript agent/MCP 层。
