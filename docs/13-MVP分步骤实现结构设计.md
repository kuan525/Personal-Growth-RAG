# MVP 分步骤实现结构设计

## 1. 这份文档的作用

这是一份中间上下文文档，用来约束后续代码实现节奏。

当前项目已经完成产品方向、长期规划和第一版 MVP 技术方案，但后续实现不能一次性生成大量代码。实现方式应改为：

- 小步推进
- 每一步都能解释清楚
- 每一步都能运行或验证
- 每一步只创建当前阶段真正需要的文件
- 每一步都保留足够注释，帮助理解代码

这份文档不是最终架构定稿，而是后续对话中实现代码时的重要上下文。

## 2. 第一版 MVP 的核心链路

第一版 MVP 的目标是打通最小 RAG 闭环：

```text
上传文档
  -> 保存文件
  -> 解析文本
  -> 切 chunk
  -> 生成 embedding
  -> 写入向量索引
  -> 提问
  -> 检索 chunk
  -> 生成回答
  -> 返回 citation
```

项目结构应该围绕这条链路设计，而不是为了“架构完整”提前拆太多层。

## 3. 推荐技术栈

### 3.1 主语言

```text
Python
```

原因：

- RAG 生态成熟。
- 文档解析、embedding、retrieval、evaluation 工具多。
- 当前阶段重点是理解和实现链路，不是做复杂工程壳。

### 3.2 API 框架

```text
FastAPI
```

原因：

- 适合 API-first MVP。
- 自动生成 Swagger 文档。
- 请求与响应结构清晰。
- 后续可以接 TUI、Web、agent 或 MCP 层。

### 3.3 数据库

```text
SQLite
```

原因：

- 本地优先。
- 不需要额外服务。
- 足够记录 document、chunk、query、answer、citation 等 metadata。

### 3.4 向量索引

```text
FAISS
```

原因：

- 本地可用。
- 适合 MVP。
- 后续如果需要删除、更新、过滤，再考虑 Qdrant。

### 3.5 模型接入

```text
OpenRouter
```

用于：

- embedding
- LLM answer

### 3.6 验证方式

当前阶段不默认引入单元测试。每一步优先通过实际启动服务、手动请求接口、查看日志等方式验证；只有在明确需要时再补 pytest 测试。

## 4. 最终第一阶段可能形成的目录结构

这是第一阶段 MVP 完成后可能形成的结构，不代表第一步就要全部创建。

```text
rag/
├── README.md
├── docs/
├── pyproject.toml
├── .env.example
├── data/
│   ├── sources/
│   └── indexes/
├── src/
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── dependencies.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── documents.py
│       │   └── questions.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── documents.py
│       │   └── questions.py
│       ├── common/
│       │   ├── __init__.py
│       │   ├── ids.py
│       │   ├── time.py
│       │   ├── hashing.py
│       │   ├── enums.py
│       │   ├── exceptions.py
│       │   └── logging.py
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py
│       │   ├── models.py
│       │   └── repositories/
│       │       └── __init__.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── parsers.py
│       │   └── service.py
│       ├── chunking/
│       │   ├── __init__.py
│       │   └── splitter.py
│       ├── embeddings/
│       │   ├── __init__.py
│       │   └── service.py
│       ├── indexing/
│       │   ├── __init__.py
│       │   └── faiss_index.py
│       ├── retrieval/
│       │   ├── __init__.py
│       │   └── service.py
│       ├── answering/
│       │   ├── __init__.py
│       │   ├── prompts.py
│       │   └── service.py
│       └── providers/
│           ├── __init__.py
│           ├── base.py
│           ├── openrouter.py
│           └── factory.py
└── tests/                  # 可选：只有明确需要单元测试时再创建
```

## 5. 每个目录的职责

### 5.1 `src/app/main.py`

FastAPI 应用入口。

负责：

- 创建 app。
- 注册路由。
- 提供 health check。
- 后续在合适阶段初始化数据库。

对应节点：

```text
API 服务启动
```

### 5.2 `src/app/config.py`

配置读取。

负责：

- OpenRouter API key。
- embedding model。
- chat model。
- database url。
- FAISS index dir。
- source dir。
- chunk size。
- top_k。

对应节点：

```text
系统配置
```

### 5.3 `src/app/api/`

API 路由层。

建议最终包含：

```text
api/
├── documents.py
└── questions.py
```

负责：

- 接收请求。
- 做轻量输入校验。
- 调用 service。
- 返回 response。

不应该在 API 层写 parse、embedding、retrieval、answering 业务逻辑。

### 5.4 `src/app/schemas/`

请求与响应结构。

建议最终包含：

```text
schemas/
├── documents.py
└── questions.py
```

负责定义：

- 上传文档响应。
- 文档列表响应。
- 问题请求。
- 问答响应。
- citation 响应。

对应节点：

```text
API contract
```

### 5.5 `src/app/storage/`

数据库层。

建议最终包含：

```text
storage/
├── database.py
├── models.py
└── repositories/
```

负责：

- 数据库连接。
- Session 管理。
- SQLAlchemy 表结构。
- 数据读写函数。

对应节点：

```text
metadata store
```

### 5.6 `src/app/ingestion/`

文档导入流程。

建议最终包含：

```text
ingestion/
├── parsers.py
└── service.py
```

负责：

- 文件解析。
- 上传后的导入状态流转。
- 调用 chunking、embedding、indexing 和 storage。

对应节点：

```text
uploaded document -> parsed text
```

### 5.7 `src/app/chunking/`

文本切分。

建议最终包含：

```text
chunking/
└── splitter.py
```

负责：

- 输入长文本。
- 输出多个 chunk。
- 保留 chunk_order。
- 支持 overlap。

对应节点：

```text
parsed text -> chunks
```

### 5.8 `src/app/embeddings/`

embedding 业务层。

建议最终包含：

```text
embeddings/
└── service.py
```

负责：

- 对 chunk 生成 embedding。
- 对 query 生成 embedding。

它不直接写 HTTP。

对应节点：

```text
chunk/query -> embedding
```

### 5.9 `src/app/providers/`

外部模型 provider。

建议最终包含：

```text
providers/
├── base.py
├── openrouter.py
└── factory.py
```

负责：

- 定义 provider 抽象接口。
- 封装 OpenRouter HTTP 调用。
- 创建 provider 实例。

核心原则：

```text
所有 OpenRouter HTTP 细节都只放在 provider 层。
```

### 5.10 `src/app/indexing/`

向量索引。

建议最终包含：

```text
indexing/
└── faiss_index.py
```

负责：

- 初始化 FAISS。
- 添加向量。
- 搜索向量。
- 保存 index 文件。

对应节点：

```text
embedding -> vector index
```

### 5.11 `src/app/retrieval/`

检索层。

建议最终包含：

```text
retrieval/
└── service.py
```

负责：

- query embedding。
- FAISS search。
- 找回 chunk。
- 记录 retrieval result。

对应节点：

```text
question -> retrieved chunks
```

### 5.12 `src/app/answering/`

回答生成。

建议最终包含：

```text
answering/
├── prompts.py
└── service.py
```

负责：

- 组织 context。
- 调用 LLM。
- 写入 answer。
- 生成 citation。

对应节点：

```text
retrieved chunks -> answer + citation
```

### 5.13 `src/app/common/`

公共工具。

建议最终包含：

```text
common/
├── ids.py
├── time.py
├── hashing.py
├── enums.py
├── exceptions.py
└── logging.py
```

负责：

- ID 生成。
- UTC 时间。
- hash。
- 状态枚举。
- 自定义异常。
- 日志配置。

对应节点：

```text
cross-cutting utilities
```

### 5.14 `tests/`

测试目录不是默认交付内容。当前项目优先通过实际启动服务、手动请求接口和日志观察来验证；只有在明确需要单元测试、回归测试或 CI 时，再创建 `tests/`。

## 6. 分步骤实现顺序

后续实现不一次性创建完整结构，而是按以下步骤推进。

### Step 1：最小工程骨架

只创建：

```text
pyproject.toml
.env.example
src/app/__init__.py
src/app/main.py
src/app/config.py
src/app/common/__init__.py
src/app/common/logging.py
```

目标：

```text
FastAPI 能启动
GET /health 返回 {"status": "ok"}
```

验收标准：

```text
1. 能安装依赖。
2. 能启动 FastAPI。
3. /health 能访问。
```

### Step 2：创建最小数据层

先创建：

```text
src/app/storage/__init__.py
src/app/storage/database.py
src/app/storage/models.py
```

第一步只实现：

```text
documents
chunks
```

暂时不急着创建全部 7 张表。

目标：

```text
SQLite 能初始化
documents 表能创建
chunks 表能创建
```

### Step 3：实现上传文档最小链路

创建：

```text
src/app/api/documents.py
src/app/schemas/documents.py
src/app/ingestion/parsers.py
src/app/chunking/splitter.py
```

目标：

```text
POST /documents 上传 txt/md
保存文件
解析文本
切 chunk
写 documents/chunks
```

这一阶段先不做 embedding 和 FAISS。

### Step 4：接 embedding + FAISS

创建：

```text
src/app/providers/
src/app/embeddings/
src/app/indexing/
```

目标：

```text
chunk -> embedding -> FAISS index
```

### Step 5：实现问答接口

创建：

```text
src/app/api/questions.py
src/app/schemas/questions.py
src/app/retrieval/
src/app/answering/
```

目标：

```text
question -> retrieve -> answer -> citation
```

## 7. 当前最重要的实现原则

### 7.1 不一次性生成大量代码

后续每次只实现一个小步骤。

每一步都要能回答：

```text
这一小步解决了什么问题？
它新增了哪些文件？
每个文件为什么存在？
怎么验证它是对的？
```

### 7.2 先最小可运行，再逐步扩展

不要为了最终架构完整，一开始就创建所有模块。

第一步只关心：

```text
项目能启动
health check 能通
测试能跑
```

### 7.3 注释要足够

当前项目代码应该保留足够注释，尤其解释：

- 为什么这么分层。
- 为什么某个状态要先落库。
- 为什么某个字段要保留。
- 失败时应该怎么处理。
- 后续扩展点在哪里。

### 7.4 日志要从一开始就保留

关键路径需要日志：

- 服务启动。
- 配置加载。
- 数据库初始化。
- 上传文档。
- 解析失败。
- chunk 数量。
- embedding 请求。
- FAISS 写入和搜索。
- 问答请求。
- citation 生成。

## 8. 下一步建议

下一步只实现 Step 1：最小工程骨架。

建议创建：

```text
pyproject.toml
.env.example
src/app/__init__.py
src/app/main.py
src/app/config.py
src/app/common/__init__.py
src/app/common/logging.py
```

不要创建 storage、ingestion、retrieval、answering 等目录。

等 Step 1 验证通过，再进入 Step 2。
