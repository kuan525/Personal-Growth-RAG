from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel


class TextChunk(BaseModel):
    chunk_order: int
    text: str


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    # 先把 chunking 封装成独立层，后续接 embedding / retrieval 时可以直接复用这里的输出。
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [TextChunk(chunk_order=index, text=chunk) for index, chunk in enumerate(chunks)]
