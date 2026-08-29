from fastapi import HTTPException, status


class AreebFetchError(Exception):
    def __init__(self, message: str, code: str = "internal_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class SecurityError(AreebFetchError):
    def __init__(self, message: str = "Security validation failed"):
        super().__init__(message, code="security_error")


class MediaAnalysisError(AreebFetchError):
    def __init__(self, message: str = "Failed to analyze media URL"):
        super().__init__(message, code="analysis_failed")


class DownloadError(AreebFetchError):
    def __init__(self, message: str = "Download failed"):
        super().__init__(message, code="download_failed")


class JobNotFoundError(AreebFetchError):
    def __init__(self, job_id: str):
        super().__init__(f"Job {job_id} not found", code="job_not_found")


class FileTooLargeError(AreebFetchError):
    def __init__(self, size_mb: float, max_mb: int):
        super().__init__(
            f"File size ({size_mb:.1f} MB) exceeds limit of {max_mb} MB",
            code="file_too_large",
        )


def to_http_exception(exc: AreebFetchError) -> HTTPException:
    mapping = {
        "security_error": status.HTTP_400_BAD_REQUEST,
        "analysis_failed": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "download_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "job_not_found": status.HTTP_404_NOT_FOUND,
        "file_too_large": status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
    }
    return HTTPException(
        status_code=mapping.get(exc.code, 500),
        detail={"error": exc.code, "message": exc.message},
    )