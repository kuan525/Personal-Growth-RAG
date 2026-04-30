from pathlib import Path

from pdfminer.high_level import extract_text


class DocumentParseError(ValueError):
    pass


def parse_document(file_path: Path, file_type: str) -> str:
    if file_type in {"txt", "md"}:
        text = file_path.read_text(encoding="utf-8")
    elif file_type == "pdf":
        text = extract_text(str(file_path))
    else:
        raise DocumentParseError(f"Unsupported file type: .{file_type}")

    if not text.strip():
        # 扫描版 PDF 或空文本都会走到这里；本阶段不做 OCR，只明确告诉调用方没有可切分文本。
        raise DocumentParseError("Parsed document is empty")

    return text
