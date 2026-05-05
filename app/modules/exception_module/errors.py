from __future__ import annotations


class B2Error(Exception):
    """Base error for B2."""


class ValidationError(B2Error):
    pass


class NotFoundError(B2Error):
    pass


class StorageError(B2Error):
    pass


class IntegrationError(B2Error):
    pass


class EvaluationError(B2Error):
    pass

