from __future__ import annotations


class SafeMediaTransferError(Exception):
    """Base exception for the application."""


class ConfigError(SafeMediaTransferError):
    """Raised when configuration is missing or invalid."""


class ValidationError(SafeMediaTransferError):
    """Raised when input validation fails."""


class ProtocolError(SafeMediaTransferError):
    """Raised when protocol framing or message validation fails."""


class TransferError(SafeMediaTransferError):
    """Raised for transfer workflow failures."""


class ResumeStateError(SafeMediaTransferError):
    """Raised when resume state is missing, corrupt, or inconsistent."""