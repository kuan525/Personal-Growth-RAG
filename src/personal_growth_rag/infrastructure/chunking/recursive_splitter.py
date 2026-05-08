from langchain_text_splitters import RecursiveCharacterTextSplitter

from personal_growth_rag.domain.documents import TextChunk


def split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[TextChunk]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "！", "？", ".", " ", ""],
    )
    chunks = splitter.split_text(text)
    return [TextChunk(chunk_order=index, text=chunk) for index, chunk in enumerate(chunks)]
