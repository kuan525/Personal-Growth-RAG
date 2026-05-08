from http import HTTPStatus


class AppError(Exception):
    error_code = "INTERNAL_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(self, message: str | None = None) -> None:
        self.message = message or "Internal error"
        super().__init__(self.message)


class BadRequestError(AppError):
    status_code = HTTPStatus.BAD_REQUEST


class NotFoundError(AppError):
    status_code = HTTPStatus.NOT_FOUND


class DocumentIngestionError(BadRequestError):
    error_code = "DOCUMENT_INGESTION_ERROR"


class DuplicateDocumentSkipped(RuntimeError):
    def __init__(self, document_id: str) -> None:
        super().__init__(f"Duplicate active document skipped: {document_id}")
        self.document_id = document_id


class DocumentNotFoundError(NotFoundError):
    error_code = "DOCUMENT_NOT_FOUND"


class SearchError(BadRequestError):
    error_code = "SEARCH_ERROR"


class QAError(BadRequestError):
    error_code = "QA_ERROR"


class ProviderError(AppError):
    error_code = "PROVIDER_ERROR"
    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
