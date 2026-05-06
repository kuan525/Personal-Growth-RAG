# Personal Growth RAG

这是一个面向个人长期使用的本地优先 RAG 项目，目标是把分散的笔记、文档、复盘、项目记录和决策材料，逐步整理成一个可检索、可引用、可持续更新的个人知识系统。

它最终想实现的不是一个简单的“文档问答工具”，而是一个围绕个人成长构建的长期知识底座：把一个人过去的学习经历、项目实践、关键选择、阶段复盘、踩坑记录、能力积累和长期目标融合起来，形成一个可以被检索、被追溯、被关联、被复盘的个人成长 RAG。

更长期看，它会接入个人图谱，把文档中的项目、技能、目标、问题、决策、资源和 evidence 连接起来。理想状态下，它像是一个融合了个人前半生阅历的本地知识系统：当你面对新的项目、学习方向或关键决策时，它能够调出相关历史，展示依据，指出风险，并帮助你做下一步判断。

当前实现会先从最小 RAG 链路开始，小步推进：

```text
document -> parse -> chunk -> metadata -> embedding -> retrieval -> answer with citations
```

## 当前实现

✅ API 服务

- FastAPI 服务骨架
- `GET /health`

✅ Documents

- `POST /documents`
- 支持 `.txt` / `.md` / `.pdf`
- 原文件保存到 `data/uploads/`

✅ Chunks

- `.txt` / `.md` 纯文本读取
- `.pdf` 使用 `pdfminer.six` 提取文本
- 使用 `RecursiveCharacterTextSplitter` 做基础 chunking
- chunk JSON 调试文件保存到 `data/chunks/`

✅ SQLite Metadata

- 使用 SQLite + SQLAlchemy
- 数据库文件：`data/app.db`
- 当前表：`documents`、`chunks`、`embeddings`
- 支持 `GET /documents`
- 支持 `GET /documents/{document_id}`

✅ Semantic Search

- 使用 DashScope `text-embedding-v4` 生成 1024 维向量
- 使用 FAISS `IndexFlatIP` 做本地向量检索
- 向量索引保存到 `data/indexes/chunks.faiss`
- 支持 `POST /search` 返回相关 chunks
- 支持本地目录批量导入

## 目标形态

这个项目长期希望形成几层能力：

1. **Evidence Retrieval**：能从个人资料中检索证据，并基于证据回答问题。
2. **Citation-based QA**：回答必须能追溯到具体 document / chunk。
3. **Incremental Knowledge Base**：资料持续新增、修改、删除时，知识库可以安全更新。
4. **Personal Knowledge Graph**：把项目、技能、目标、问题、决策、资源和 evidence 连接起来。
5. **Memory & Review**：从复盘和项目记录中沉淀长期 memory，例如经验、偏好、反复问题和阶段目标。
6. **Decision Support**：在关键选择上，基于历史经历和 evidence 给出有边界的分析、风险和下一步建议。

核心原则：

```text
Evidence before opinion.
Traceability before intelligence.
Local-first before platform.
Small steps before big architecture.
```

## 技术栈

- Python 3.11
- FastAPI
- Pydantic / pydantic-settings
- SQLAlchemy
- SQLite
- DashScope text-embedding-v4
- FAISS
- pdfminer.six
- LangChain text splitters
- Ruff

## 项目结构

```text
src/app/
├── api/          # API 路由
├── chunking/     # 文本切分
├── common/       # 通用能力
├── ingestion/    # 上传、解析、chunk、入库
├── schemas/      # API 响应模型
├── storage/      # SQLAlchemy database / models
├── embeddings/   # embedding provider
├── indexing/     # FAISS index
├── search/       # semantic search
├── cli/          # 本地命令
├── config.py     # 配置
└── main.py       # FastAPI 入口
```

运行后生成本地数据：

```text
data/
├── app.db        # SQLite metadata
├── uploads/      # 原始上传文件
├── chunks/       # chunk JSON 调试文件
└── indexes/      # FAISS index 文件
```

`data/` 不进入 Git。

## 本地运行

安装依赖：

```bash
pip install -e ".[dev]"
```

配置环境变量：

```bash
cp .env.example .env
# 然后在 .env 中填写 DASHSCOPE_API_KEY
```

启动服务：

```bash
uvicorn src.app.main:app --reload
```

接口文档：

```text
http://127.0.0.1:8000/docs
```

## API 示例

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

上传文档：

```bash
curl -X POST "http://127.0.0.1:8000/documents" \
  -F "file=@/path/to/document.pdf"
```

查询文档列表：

```bash
curl -s http://127.0.0.1:8000/documents | python -m json.tool
```

查询文档详情：

```bash
curl -s http://127.0.0.1:8000/documents/doc_xxx | python -m json.tool
```

语义检索：

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query_text":"我有哪些后端开发经历？","top_k":5}'
```

批量导入本地目录：

```bash
python -m src.app.cli.ingest_dir /path/to/docs
```

查看 SQLite：

```bash
sqlite3 data/app.db ".tables"
sqlite3 data/app.db "SELECT id, source_name, status, chunk_count FROM documents;"
```


## 重置本地数据与重建索引

如果想让历史文档重新走完整链路：

```text
parse -> chunk -> SQLite -> embedding -> FAISS
```

推荐做一次本地数据重置，然后用批量导入重新导入原始文档目录。

### 方式一：完全重置，重新导入原始资料

这会删除本地数据库、上传副本、chunk JSON 和 FAISS index：

```bash
rm -rf data/app.db data/uploads data/chunks data/indexes
```

然后重新启动服务，或直接执行批量导入：

```bash
python -m src.app.cli.ingest_dir /path/to/original/docs
```

其中 `/path/to/original/docs` 应该是你真正保存原始资料的目录，而不是 `data/uploads/`。

导入完成后可以测试检索：

```bash
curl -s -X POST "http://127.0.0.1:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query_text":"我有哪些后端开发经历？","top_k":5}' \
  | python -m json.tool
```

### 方式二：只删除 SQLite 和 FAISS

如果你只想清掉 metadata 和向量索引，但保留 `data/uploads/`、`data/chunks/` 文件，可以执行：

```bash
rm -f data/app.db
rm -rf data/indexes
```

但注意：删除 SQLite 后，系统不再知道 `data/uploads/` 里的文件对应哪些 document。推荐仍然从原始资料目录重新批量导入。

### 注意

- `data/` 是本地运行数据，不进入 Git。
- `.env` 里的 `DASHSCOPE_API_KEY` 不要删除，除非你要重新配置 key。
- 旧版本中已经存在但没有 embedding 的文档，不会自动进入 FAISS；需要通过重新导入或后续 backfill 命令处理。

## 下一步

优先实现完整问答闭环：

1. `POST /questions`
2. retrieval trace
3. answer with citations
4. query_runs / retrieval_results / answers / citations 落库

之后再逐步推进：

- 增量更新
- 个人图谱
- memory / review
- decision support
- evaluation / regression

更多内部规划见 `docs/`。

## 开发

运行代码检查：

```bash
ruff check .
```
