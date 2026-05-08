from personal_growth_rag.domain.retrieval import RetrievedChunk

SYSTEM_PROMPT = """你是 Personal Growth RAG 的问答助手。
你必须只基于用户提供的 context 回答问题，不要使用外部知识或猜测。
如果 context 不足以支持答案，必须明确说“现有资料不足以回答这个问题”。
回答要简洁、具体，并尽量在关键结论后标注引用编号，例如 [1]、[2]。
不要编造引用编号，不要编造文档来源。"""


def build_question_prompt(question: str, citations: list[RetrievedChunk]) -> str:
    context_blocks = []
    for index, citation in enumerate(citations, start=1):
        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] source_name={citation.source_name}",
                    f"document_id={citation.document_id}",
                    f"chunk_id={citation.chunk_id}",
                    f"chunk_order={citation.chunk_order}",
                    f"score={citation.score:.4f}",
                    "text:",
                    citation.text,
                ]
            )
        )

    context = "\n\n---\n\n".join(context_blocks)
    return f"""问题：{question}

Context：
{context}

请基于上面的 Context 回答问题。"""
