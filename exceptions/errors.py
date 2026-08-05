"""
Custom exception hierarchy for the project planner application.

All application-raised errors inherit from AppError so calling code can
catch broadly (`except AppError`) or narrowly (`except NotFoundError`).
Each exception carries a plain-English `.message` describing what went
wrong, since there is no HTTP layer to translate errors into status codes.
"""


class AppError(Exception):
    """Base class for all application-specific errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class ValidationError(AppError):
    """Raised when input data is malformed, missing, or violates a field
    constraint (e.g. required field missing, value exceeds max length,
    wrong type)."""


class NotFoundError(AppError):
    """Raised when a referenced entity (user, team, board, task) does not
    exist."""


class ConflictError(AppError):
    """Raised when an operation would violate a uniqueness constraint
    (e.g. duplicate user name, duplicate board name within a team)."""


class InvalidStateError(AppError):
    """Raised when an operation is not allowed given an entity's current
    state (e.g. closing a board with incomplete tasks, adding a task to
    a closed board)."""
