from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str
    code: str
    status_code: int = 500


class ValidationAppError(AppError):
    def __init__(self, message: str, code: str = "VALIDATION_ERROR") -> None:
        super().__init__(message=message, code=code, status_code=422)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED") -> None:
        super().__init__(message=message, code=code, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN") -> None:
        super().__init__(message=message, code=code, status_code=403)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found", code: str = "NOT_FOUND") -> None:
        super().__init__(message=message, code=code, status_code=404)


class DependencyError(AppError):
    def __init__(self, message: str, code: str = "DEPENDENCY_ERROR") -> None:
        super().__init__(message=message, code=code, status_code=503)


class UpstreamServiceError(AppError):
    def __init__(self, message: str, code: str = "UPSTREAM_SERVICE_ERROR") -> None:
        super().__init__(message=message, code=code, status_code=502)
