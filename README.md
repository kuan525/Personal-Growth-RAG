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
- 当前表：`documents`、`chunks`
- 支持 `GET /documents`
- 支持 `GET /documents/{document_id}`

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
├── config.py     # 配置
└── main.py       # FastAPI 入口
```

运行后生成本地数据：

```text
data/
├── app.db        # SQLite metadata
├── uploads/      # 原始上传文件
└── chunks/       # chunk JSON 调试文件
```

`data/` 不进入 Git。

## 本地运行

安装依赖：

```bash
pip install -e ".[dev]"
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

查看 SQLite：

```bash
sqlite3 data/app.db ".tables"
sqlite3 data/app.db "SELECT id, source_name, status, chunk_count FROM documents;"
```

## 下一步

优先实现最小 RAG 闭环：

1. embedding service
2. FAISS 向量索引
3. `POST /questions`
4. retrieval trace
5. answer with citations

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
