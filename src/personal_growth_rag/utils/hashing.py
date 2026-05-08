import hashlib


def hash_bytes(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
