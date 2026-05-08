from uuid import uuid4


def new_document_id() -> str:
    return f"doc_{uuid4().hex}"


def new_chunk_id() -> str:
    return f"chk_{uuid4().hex}"
