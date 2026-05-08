import argparse
import logging
from pathlib import Path

from personal_growth_rag.application.documents.ingest_document import ingest_local_file
from personal_growth_rag.core.config import get_settings
from personal_growth_rag.core.constants import ALLOWED_FILE_TYPES
from personal_growth_rag.core.errors import DocumentIngestionError, DuplicateDocumentSkipped
from personal_growth_rag.core.logging import setup_logging
from personal_growth_rag.infrastructure.db.session import get_session_factory, init_db

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a local directory into Personal Growth RAG."
    )
    parser.add_argument("directory", type=Path, help="Directory containing .txt/.md/.pdf files")
    args = parser.parse_args()

    settings = get_settings()
    setup_logging(settings)
    init_db(settings)

    directory = args.directory
    if not directory.exists() or not directory.is_dir():
        raise SystemExit(f"Directory does not exist: {directory}")

    stats = {"processed": 0, "created": 0, "skipped": 0, "failed": 0}
    session_factory = get_session_factory(settings)

    with session_factory() as db:
        for file_path in iter_supported_files(directory):
            stats["processed"] += 1
            try:
                response = ingest_local_file(file_path, settings, db, skip_duplicate=True)
                stats["created"] += 1
                logger.info(
                    "Created document: path=%s document_id=%s",
                    file_path,
                    response.document_id,
                )
            except DuplicateDocumentSkipped as error:
                stats["skipped"] += 1
                logger.info(
                    "Skipped duplicate: path=%s document_id=%s",
                    file_path,
                    error.document_id,
                )
            except DocumentIngestionError as error:
                stats["failed"] += 1
                logger.warning("Failed to ingest: path=%s error=%s", file_path, error)

    print(
        "Ingest summary: "
        f"processed={stats['processed']} "
        f"created={stats['created']} "
        f"skipped={stats['skipped']} "
        f"failed={stats['failed']}"
    )


def iter_supported_files(directory: Path) -> list[Path]:
    supported_suffixes = {f".{file_type}" for file_type in ALLOWED_FILE_TYPES}
    return sorted(
        file_path
        for file_path in directory.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in supported_suffixes
    )


if __name__ == "__main__":
    main()
