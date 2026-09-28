"""
database/exceptions.py — Domain Exception Hierarchy
=====================================================
Structured exceptions for database operations.
Callers can catch these for fine-grained error handling without
being coupled to sqlite3 internals.

NOTE: Existing code continues to catch ``Exception`` and return
empty DataFrames for backward compatibility.  These exception
classes are used for *new* code and for *logging context* —
they are never thrown in a way that changes existing behavior.
"""


class AgriIntelDBError(Exception):
    """Base exception for all AgriIntel database errors."""


class ConnectionError(AgriIntelDBError):
    """Failed to establish or reuse a database connection."""


class DataValidationError(AgriIntelDBError):
    """Data failed validation before a write operation.

    Attributes:
        field: The field that failed validation.
        detail: Human-readable explanation.
    """

    def __init__(self, message: str, *, field: str = "", detail: str = ""):
        super().__init__(message)
        self.field = field
        self.detail = detail


class QueryError(AgriIntelDBError):
    """A SQL query or statement failed."""


class MigrationError(AgriIntelDBError):
    """A schema migration step failed."""
