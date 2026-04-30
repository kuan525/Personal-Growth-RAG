# Personal Growth RAG

这是一个面向个人长期使用的本地优先 RAG 项目，目标是把分散的笔记、文档、复盘、项目记录和决策材料，逐步整理成一个可检索、可引用、可持续更新的个人知识系统。

长期方向上，它不只是一个文档问答 demo，而是希望成为一个围绕个人成长、项目推进、阶段复盘和关键决策的知识辅助系统。

## 当前实现

当前项目处于早期 MVP 阶段，已经实现了最小 API 服务和文件导入链路：

- 基于 FastAPI 的 API 服务骨架
- `/health` 健康检查接口
- `/documents` 单文件上传接口
- 支持上传 `.txt`、`.md`、`.pdf`
- 上传文件保存到本地 `data/uploads/`
- 解析后的 chunk 保存到本地 `data/chunks/`
- `.txt` / `.md` 使用纯文本读取
- `.pdf` 使用 `pdfminer.six` 提取文本
- 使用 `RecursiveCharacterTextSplitter` 做基础 chunking

当前生成的数据都在本地 `data/` 目录下，该目录不会进入 Git。

## 技术栈

当前主要使用：

- Python 3.11
- FastAPI
- Pydantic / pydantic-settings
- pdfminer.six
- LangChain text splitters
- Ruff

## 项目结构

```text
src/app/
├── api/          # API 路由
├── chunking/     # 文本切分
├── common/       # 通用能力
├── ingestion/    # 文件上传、解析和导入流程
├── schemas/      # API 响应模型
├── config.py     # 配置
└── main.py       # FastAPI 入口
```

运行后会生成本地数据目录：

```text
data/
├── uploads/      # 原始上传文件
└── chunks/       # chunk JSON 文件
```

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

示例响应：

```json
{
  "document_id": "doc_xxx",
  "source_name": "document.pdf",
  "file_type": "pdf",
  "status": "active",
  "stored_path": "data/uploads/doc_xxx.pdf",
  "chunk_path": "data/chunks/doc_xxx.json",
  "chunk_count": 8,
  "error_message": null
}
```

## 后续方向

后续会围绕 RAG 的完整链路继续演进，包括本地知识库、embedding、向量检索、citation-based QA、增量更新、个人知识图谱、长期 memory 和决策辅助。

整体方向是先把最小 RAG 闭环做稳定，再逐步扩展成一个可长期使用的个人知识系统。

## 开发

运行代码检查：

```bash
ruff check .
```
