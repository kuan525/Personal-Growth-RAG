# 元数据与存储规格说明

## 1. 文档目的

本文件定义系统中的核心元数据字段、标识规则、索引持久化假设以及文档更新时的存储行为约定。

其目标是避免系统随着阶段演进后，文档、chunk、索引与引用关系变得混乱或不可追踪。

## 2. 设计原则

元数据与存储设计应满足以下原则：

- 可追溯：回答能追到 chunk，chunk 能追到文档
- 稳定：同一文档更新前后关系清晰
- 最小必要：先保留高价值字段，不做无用堆砌
- 服务产品：字段设计必须为检索、引用、评测和运维服务

## 3. document_id 规则

### 要求

- 每个进入系统的文档都应有唯一 document_id
- document_id 应在系统内部稳定可引用
- 同一文档更新时，应有明确策略决定是否沿用 document_id

### 建议策略

可基于以下信息组合生成或管理：

- source_path
- 文件名
- 文件指纹 / hash
- 导入时间

### 目标

确保用户能明确知道：

- 这份文档是谁
- 它是否是旧版本
- 它与哪些 chunk、引用有关

## 4. chunk_id 规则

### 要求

- 每个 chunk 应有唯一 chunk_id
- chunk_id 能关联回 document_id
- chunk_id 对应具体 chunk 顺序或结构位置

### 建议包含信息

- document_id
- chunk_order
- 结构路径或页码信息（如果有）

## 5. 文档级元数据字段

建议文档级至少保留以下字段：

- document_id
- source_path
- source_name
- file_type
- file_size
- last_modified_at
- parser_type
- ingest_time
- status

### 可选扩展字段

- version_tag
- file_hash
- corpus_name
- parse_quality_flag

## 6. chunk 级元数据字段

建议 chunk 级至少保留以下字段：

- chunk_id
- document_id
- chunk_text
- chunk_order
- source_path
- file_type
- parser_type

### 若可获取，建议补充

- page_number
- heading_path
- section_label
- block_type
- start_offset / end_offset

## 7. 检索结果级记录字段

为支持评测和调试，建议检索结果至少保留：

- query_text
- retrieved_chunk_ids
- retrieval_scores
- retrieval_source
- final_selected_chunks
- final_answer_id 或结果记录 ID

## 8. 索引持久化假设

### 当前阶段建议

- 支持本地索引持久化
- 用户可区分“已建立索引”和“需要重建索引”的状态
- 索引与文档版本关系可追踪

### 当前不要求

- 分布式索引服务
- 多租户隔离
- 企业级备份系统

## 9. 文档更新规则

### 目标

避免用户更新文档后，系统继续使用旧内容且无法感知。

### 建议规则

- 文档更新后应标记需要重新处理或重新索引
- 重新索引后应清晰替换旧内容或明确版本并存策略
- 不允许默默混入旧新两份内容导致问答混乱

## 10. 文档删除规则

### 目标

当文档被删除后，系统不应长期继续引用失效内容。

### 建议规则

- 支持删除对应 document_id 及其关联 chunk 的索引记录
- 或至少标记为不可用状态

## 11. corpus / collection 规则

如果后续引入 corpus 或 collection 概念，建议至少定义：

- corpus_id / corpus_name
- 文档与 corpus 的归属关系
- 当前查询作用范围

前期可先轻量实现，不必一次做成复杂多库系统。

## 12. 存储异常风险

需要重点避免以下问题：

- 文档更新后旧索引仍长期生效但无提示
- chunk 引用无法回到原始文档
- document_id 与 source_path 关系混乱
- 引用展示与实际检索内容不一致

## 13. 验收建议

本规格应至少支持以下能力：

- 回答可以追溯到具体文档和 chunk
- 文档更新与删除有清晰行为
- 索引持久化状态可被管理
- 元数据足以支撑引用与评测

## 14. 与后续阶段关系

- Phase 1：建立最基础的 document / chunk 关系
- Phase 3：增强 page / heading / section 等元数据
- Phase 4：用于管理文档更新与索引状态
- Phase 5：用于评测结果追踪与回归分析

因此，这份规格是系统长期保持一致性的底层约束之一。
