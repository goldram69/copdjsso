# apps/discourse/exceptions.py
class SSOValidationError(Exception):
    """Exception raised when SSO payload validation fails."""

    pass
