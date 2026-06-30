class AppError(Exception):
    status_code = 400

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.message)


class AuthError(AppError):
    def __init__(self, message: str = "Authentication failed", status_code: int = 401):
        super().__init__(message, status_code)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Access denied", status_code: int = 403):
        super().__init__(message, status_code)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found", status_code: int = 404):
        super().__init__(message, status_code)


class ValidationError(AppError):
    def __init__(self, message: str = "Validation failed", status_code: int = 422):
        super().__init__(message, status_code)


class ElectionError(AppError):
    pass


class VoteError(AppError):
    pass


class FileError(AppError):
    pass
