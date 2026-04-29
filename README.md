# 个人成长型 RAG

这是一个面向个人长期使用的 **Personal Growth RAG** 项目。

它不是普通 RAG demo，也不是单纯的本地文档问答工具。它的目标是构建一个本地优先、可增量更新、带个人图谱和长期 memory 的个人知识系统，最终能在学习、项目推进、阶段复盘和关键决策时，基于历史资料和 evidence 给出有边界、可追溯的建议。

## 1. 项目目标

这个项目最终要实现的是：

> 把分散的个人资料、项目记录、复盘、决策、学习笔记和经验沉淀，转化为一个可检索、可引用、可关联、可更新、可辅助决策的个人知识系统。

系统会从最基础的 RAG 问答开始，逐步成长为：

1. **Citation-based QA**：能回答文档问题，并给出 citation。
2. **Incremental Knowledge Base**：新增、修改、删除资料时，不需要每次全量重建。
3. **Personal Knowledge Graph**：连接 project、skill、goal、problem、decision、resource、evidence。
4. **Memory and Review System**：从 weekly review、project review、decision log 中沉淀长期 memory。
5. **Decision Support**：在具体实践或时间节点，基于历史 evidence 辅助判断下一步。

## 2. 当前结论：推荐技术路线

### 2.1 不建议一开始用 Rust + TypeScript 全栈

你未来想接入 agent，并且想要 TUI，这个方向没有问题，但 **不建议第一阶段就用 Rust + TypeScript 作为主实现栈**。

原因：

- RAG 的早期核心难点不是 TUI，也不是系统性能，而是 ingestion、chunking、embedding、retrieval、rerank、evaluation、incremental update。
- Python 在 RAG 生态里最成熟，适合快速验证 pipeline。
- 个人图谱、memory、evaluation、LLM extraction 这些能力，用 Python 实现速度更快。
- 过早引入 Rust + TS 会把精力分散到工程结构、跨语言调用、构建系统和 UI，而不是验证 RAG 核心链路。

### 2.2 推荐主路线：Python Core + Rust TUI + TypeScript Agent/UI

更合理的技术路线是分层：

```text
Python:      RAG core / ingestion / retrieval / graph / memory / evaluation
SQLite:      metadata / graph / memory / decision / eval records
FAISS:       Phase 1 vector index
Qdrant:      Phase 4+ vector index with update/delete/filter
OpenRouter:  embedding + LLM provider in MVP
Rust:        TUI shell, later stage
TypeScript:  Agent integration / web UI / MCP-style interface, later stage
```

也就是说：

- **先用 Python 做 core engine**
- **等 core 稳定后，用 Rust 做 TUI**
- **需要接入 agent 或 Web / MCP / API 时，再用 TypeScript 做外层接口**

### 2.3 为什么不是纯 Python

纯 Python 可以完成 MVP，但长期来看你想要：

- TUI
- agent 接入
- 更好的本地工具体验
- 可能的长期产品化

所以最终不应该只有 Python。

但 Python 应该是 core 的第一语言，因为它最适合快速做 RAG 迭代。

### 2.4 为什么 Rust 适合 TUI

Rust 适合做后期 TUI，因为：

- `ratatui` 生态成熟
- 单二进制分发体验好
- 终端交互性能好
- 适合做本地工具 shell
- 可以调用 Python core 提供的 CLI / HTTP / IPC 接口

但 Rust 不适合作为第一阶段 RAG core 的主语言，因为 embedding、retrieval、LLM workflow、evaluation 生态没有 Python 高效。

### 2.5 为什么 TypeScript 适合 Agent/UI 层

TypeScript 适合后期做：

- Web UI
- agent-facing API
- MCP server
- 与前端或桌面壳集成
- LangGraph / workflow / external integration 层

但 TypeScript 也不建议作为第一阶段 core，因为本项目早期最重要的是快速验证 RAG 质量，而不是构建前端或 agent 平台。

## 3. 推荐阶段技术栈

### Phase 0：基础数据集准备

目标：准备真实 documents 和 validation questions。

技术：

- Markdown / JSONL
- 手工整理 validation set

不需要复杂工程。

### Phase 1：Local RAG MVP

目标：跑通本地文档问答闭环。

推荐技术：

- Python
- SQLite
- FAISS
- PyMuPDF / markdown parser
- OpenRouter Embedding API
- OpenRouter Chat API
- API-first

交付能力：

- ingest documents
- generate chunks
- build vector index
- query
- answer with citations
- record query logs

### Phase 2：Retrieval Quality

目标：提升 retrieval 命中率。

推荐技术：

- Python
- BM25 / SQLite FTS
- hybrid retrieval
- rerank model / rerank API
- evaluation runner

交付能力：

- dense + sparse retrieval
- rerank
- baseline comparison
- failure taxonomy

### Phase 3：Structured Ingestion

目标：提升 parsing 和 chunk quality。

推荐技术：

- Python
- PyMuPDF / pdfplumber
- Markdown AST parser
- structured blocks
- metadata enrichment

交付能力：

- block-level intermediate representation
- heading / page metadata
- structured chunking
- parse diagnostics

### Phase 4：Incremental Knowledge Base

目标：让资料能长期增量维护。

推荐技术：

- Python
- SQLite
- Qdrant
- content hash tracking
- index invalidation

交付能力：

- add / update / delete documents
- active / superseded / deleted chunk status
- vector index update
- status report

### Phase 5：Personal Graph MVP

目标：建立个人图谱。

推荐技术：

- Python
- SQLite graph tables
- LLM extraction
- entity / relation schema

交付能力：

- extract entities
- extract relations
- evidence-backed graph
- graph-assisted retrieval

早期不建议直接上 Neo4j，SQLite 足够。

### Phase 6：Memory and Review

目标：从复盘和决策记录中沉淀 memory。

推荐技术：

- Python
- SQLite
- Markdown review templates
- LLM extraction

交付能力：

- review ingestion
- memory candidates
- time-based summary
- repeated problem detection

### Phase 7：Decision Support

目标：基于历史 evidence 辅助决策。

推荐技术：

- Python core
- structured prompts
- memory + graph + retrieval context
- decision records

交付能力：

- option comparison
- recommendation with evidence
- risk and missing information
- decision review

### Phase 8：TUI / Agent Integration

目标：把成熟 core 接入更好的使用界面和 agent 系统。

推荐技术：

- Rust + ratatui：TUI
- TypeScript：agent / MCP / Web UI / API integration
- Python core 作为 engine

交付能力：

- TUI 操作知识库
- agent 调用 RAG core
- query / memory / decision API
- 本地工具化体验

## 4. 最终推荐架构

最终可以演进成：

```text
                ┌──────────────────────────┐
                │ Rust TUI                 │
                │ ratatui                  │
                └────────────┬─────────────┘
                             │ CLI / HTTP / IPC
┌────────────────────────────▼────────────────────────────┐
│ Python Core Engine                                      │
│ ingestion / chunking / retrieval / graph / memory        │
│ decision support / evaluation                           │
└───────────────┬──────────────────────────────┬──────────┘
                │                              │
        ┌───────▼────────┐             ┌───────▼────────┐
        │ SQLite          │             │ Qdrant / FAISS │
        │ metadata/graph  │             │ vector index   │
        │ memory/eval     │             │                │
        └────────────────┘             └────────────────┘

                ┌──────────────────────────┐
                │ TypeScript Layer          │
                │ Agent / MCP / Web UI      │
                └──────────────────────────┘
```

## 5. 为什么这个顺序最合理

如果一开始用 Rust + TypeScript 全栈，会更像在做产品壳，而不是验证核心价值。

本项目最核心的不确定性是：

- ingestion 后内容质量如何
- chunk 怎么切才有效
- retrieval 是否命中 evidence
- citation 是否可信
- incremental update 是否安全
- graph 是否真的改善问题
- memory 是否能辅助 review
- decision support 是否比泛泛建议更有用

这些问题都应该优先用 Python 快速验证。

等 Python core 证明价值后，再把 Rust TUI 和 TypeScript agent layer 接上，才是更稳的工程路线。

## 6. 文档结构

当前核心文档在 `docs/` 下平铺存放：

```text
docs/00-项目总蓝图.md
docs/01-产品需求文档.md
docs/02-系统架构设计.md
docs/03-数据模型设计.md
docs/04-实施路线图.md
docs/05-校验方案.md
docs/06-增量更新设计.md
docs/07-个人图谱设计.md
docs/08-记忆与复盘设计.md
docs/09-决策辅助设计.md
docs/10-阶段执行手册.md
docs/11-最小API版本实现清单.md
docs/12-第一版MVP实现技术方案.md
```

建议阅读顺序就是编号顺序。

## 7. MVP 本地运行

第一版 API MVP 已经按 `docs/12-第一版MVP实现技术方案.md` 落地，包含：

- `POST /documents`：上传并索引文档
- `GET /documents`：查看文档列表
- `GET /documents/{document_id}`：查看单个文档状态
- `POST /questions`：基于已上传文档问问题并返回 citation

准备环境变量：

```bash
cp .env.example .env
```

编辑 `.env`，填入真实 OpenRouter 配置：

```env
OPENROUTER_API_KEY=你的 OpenRouter key
OPENROUTER_EMBEDDING_MODEL=你的 embedding model
OPENROUTER_CHAT_MODEL=你的 chat model
```

安装依赖：

```bash
pip install -e ".[dev]"
```

启动 API：

```bash
uvicorn src.app.main:app --reload
```

运行测试：

```bash
pytest
```

## 8. 当前最应该做什么

当前不应该直接做 TUI、agent integration、graph 或 decision support。

当前应该做：

1. 准备 Phase 0 validation set。
2. 整理真实 documents。
3. 写 20 个 validation questions。
4. 标注 expected sources 和 refusal expectations。
5. 用 Python 实现 Phase 1 Local RAG MVP。
6. 跑第一次 baseline evaluation。

只有 baseline 跑出来后，才知道 retrieval、parsing、incremental update、graph、memory 应该怎么继续优化。

## 9. 最终结论

### 语言结论

- **RAG core：Python**
- **metadata / graph / memory / eval store：SQLite**
- **MVP vector index：FAISS**
- **长期 vector index：Qdrant**
- **MVP model provider：OpenRouter（embedding + LLM）**
- **TUI：Rust + ratatui**
- **Agent / MCP / Web integration：TypeScript**

### 战略结论

不要一开始追求 Rust + TypeScript 全栈。

最合理路线是：

```text
Python Core MVP
  -> Retrieval / Incremental / Graph / Memory 稳定
  -> Rust TUI
  -> TypeScript Agent / MCP / Web Layer
```

这条路线既能最快验证 RAG 核心价值，也不会牺牲你未来想做 TUI 和 agent integration 的方向。
