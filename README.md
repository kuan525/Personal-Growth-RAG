# Personal Growth RAG

这是一个面向个人长期使用的本地优先 RAG 项目，目标是把分散的笔记、文档、复盘、项目记录和决策材料，逐步整理成一个可检索、可引用、可持续更新、可复盘的个人知识系统。

它不是普通“文档问答 demo”，而是个人成长知识底座：先从真实资料中检索 evidence，再基于 evidence 回答，并逐步扩展到 query trace、memory、personal graph 和 decision support。

核心链路：

```text
document -> parse -> chunk -> metadata -> embedding -> retrieval -> answer with citations
```

核心原则：

```text
Evidence before opinion.
Traceability before intelligence.
Local-first before platform.
Small steps before big architecture.
```

## 当前实现

✅ Documents & Ingestion

支持 `.txt` / `.md` / `.pdf` 上传与本地目录批量导入，原文件保存到 `data/uploads/`，可维护 `data/library/` 作为个人原始资料库。

✅ Chunking & Metadata

支持文本解析、基础 chunking，并通过 SQLite + SQLAlchemy 持久化 `documents` / `chunks` / `embeddings` 元数据，chunk JSON 调试文件保存到 `data/chunks/`。

✅ Retrieval

已接入 DashScope `text-embedding-v4` + FAISS `IndexFlatIP`，完成 chunk embedding、本地向量索引持久化和语义相似度检索。

✅ Search API

新增 `POST /v1/search`，支持 query -> relevant chunks，返回可追溯的 document / chunk evidence。

✅ Questions MVP

新增 `POST /v1/questions`，接入 DeepSeek V4 Pro，完成 retrieval -> answer with citations 的最小 RAG 问答闭环。

🚧 Next step

实现 Question Trace MVP，将 question / retrieval results / answer / citations 落库，让每次回答都可回放、可评估、可复盘，为后续 memory 和 decision support 打基础。

## 技术栈

- Python 3.11
- FastAPI
- Pydantic / pydantic-settings
- SQLAlchemy + SQLite
- DashScope text-embedding-v4
- FAISS
- OpenAI SDK compatible API
- DeepSeek V4 Pro
- pdfminer.six
- LangChain text splitters
- Ruff

## 项目结构

```text
src/personal_growth_rag/
├── api/v1/          # HTTP routes + request/response contracts
├── application/     # 业务用例和主数据流
├── domain/          # 轻量业务概念、prompt、稳定规则
├── infrastructure/  # SQLite、FAISS、DashScope、DeepSeek、parser、chunker
├── core/            # 配置、日志、错误、路径、常量
├── cli/             # 本地命令入口
├── utils/           # hash、id、time 等无状态工具
└── main.py          # FastAPI app factory
```

运行后生成本地数据：

```text
data/
├── app.db
├── uploads/
├── chunks/
└── indexes/
```

`data/` 和 `.env` 不进入 Git；`docs/` 作为正式项目文档进入 Git。

## 本地运行

安装依赖：

```bash
pip install -e ".[dev]"
```

配置环境变量：

```bash
cp .env.example .env
# 填写 DASHSCOPE_API_KEY 和 DEEPSEEK_API_KEY
```

启动服务：

```bash
uvicorn personal_growth_rag.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## API 示例

健康检查：

```bash
curl -s http://127.0.0.1:8000/v1/health | python -m json.tool
```

上传文档：

```bash
curl -X POST "http://127.0.0.1:8000/v1/documents" \
  -F "file=@/path/to/document.pdf"
```

查询文档列表：

```bash
curl -s http://127.0.0.1:8000/v1/documents | python -m json.tool
```

查询文档详情：

```bash
curl -s http://127.0.0.1:8000/v1/documents/doc_xxx | python -m json.tool
```

语义检索：

```bash
curl -s -X POST http://127.0.0.1:8000/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query_text":"我有哪些后端开发经历？","top_k":5}' | python -m json.tool
```

RAG 问答：

```bash
curl -s -X POST http://127.0.0.1:8000/v1/questions \
  -H "Content-Type: application/json" \
  -d '{"question":"我有哪些后端开发经历？","top_k":5}' | python -m json.tool
```

批量导入本地目录：

```bash
python -m personal_growth_rag.cli.ingest_dir /path/to/docs
```

## 重置本地数据与重建索引

如果想让历史文档重新走完整链路：

```text
parse -> chunk -> SQLite -> embedding -> FAISS
```

可以删除本地运行数据后重新导入：

```bash
rm -rf data/app.db data/uploads data/chunks data/indexes
python -m personal_growth_rag.cli.ingest_dir /path/to/original/docs
```

注意：`data/uploads/` 是系统保存的上传副本，不建议作为唯一原始资料库；更推荐维护一个独立原始目录，例如 `data/library/`。

## 开发检查

```bash
ruff check .
```

## 结构约定

项目按“入口 -> 用例 -> 领域概念 -> 基础设施”组织：`api/v1` 只负责 HTTP 接入和契约，`application` 负责可复用业务用例，`domain` 放稳定概念和 prompt，`infrastructure` 封装 SQLite / FAISS / DashScope / DeepSeek / parser 等具体实现。CLI、后续 jobs、evaluation 不调用 API，而是直接复用 application。

```text
API / CLI
  -> application use case
    -> domain data / prompt
    -> infrastructure provider / repository / vectorstore
```

当前最重要的三条用例链路：

```text
ingest_document: file -> parse -> chunk -> SQLite -> embedding -> FAISS
search_chunks: query -> query embedding -> FAISS -> SQLite hydrate -> evidence chunks
answer_question: question -> retrieval -> prompt -> DeepSeek -> answer + citations
```

API 成功和失败都统一返回 envelope：

成功：

```json
{
  "success": true,
  "error_code": null,
  "message": "ok",
  "data": {},
  "request_id": null
}
```

失败：

```json
{
  "success": false,
  "error_code": "DOCUMENT_NOT_FOUND",
  "message": "Document not found",
  "data": null,
  "request_id": null
}
```

这样前端只需要先判断 `success`；失败时读取 `error_code/message`，成功时读取 `data`。


Document API 的成功响应只暴露文档公开字段，例如 `document_id/source_name/file_type/status/chunk_count/created_at/updated_at`。本地排障字段如 `stored_path/chunk_path/error_message` 保留在 SQLite，不放进成功态 `data`，避免前端把内部实现细节当产品字段依赖。
