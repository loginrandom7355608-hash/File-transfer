from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import puremagic

from app.validation.extension_policy import ExtensionPolicy

logger = logging.getLogger(__name__)

# How many bytes to read from the start and end of a file for signature
# detection. This is generous enough for every format puremagic recognizes
# (including formats that store their signature near the end, like some
# MP4/MOV container variants), while remaining tiny relative to multi-GB
# video files. Reading a bounded amount like this means a 10GB file takes
# the same, near-instant time to inspect as a 10KB file.
_HEADER_BYTES = 4096
_FOOTER_BYTES = 4096


@dataclass(slots=True)
class SignatureResult:
    decision: str
    reason: str
    detected_extension: str | None = None
    mime_type: str | None = None
    warnings: list[str] = field(default_factory=list)

    @classmethod
    def allow_unknown(cls) -> "SignatureResult":
        return cls(decision="allow", reason="signature_check_disabled")

    @classmethod
    def allow(cls, *, detected_extension: str | None, mime_type: str | None, warnings: list[str] | None = None) -> "SignatureResult":
        return cls(
            decision="allow",
            reason="allowed",
            detected_extension=detected_extension,
            mime_type=mime_type,
            warnings=warnings or [],
        )

    @classmethod
    def reject(cls, reason: str, *, detected_extension: str | None = None, mime_type: str | None = None) -> "SignatureResult":
        return cls(
            decision="reject",
            reason=reason,
            detected_extension=detected_extension,
            mime_type=mime_type,
        )


def _read_bounded_sample(path: Path) -> bytes:
    """
    Read a bounded sample of a file's bytes for signature detection:
    the first _HEADER_BYTES and the last _FOOTER_BYTES.

    This is deliberately bounded I/O: regardless of whether the file is
    10KB or 10GB, we only ever touch a few KB of data. That keeps signature
    verification fast for large video files without skipping the check.
    """
    size = path.stat().st_size

    with path.open("rb") as handle:
        header = handle.read(_HEADER_BYTES)

        if size <= _HEADER_BYTES + _FOOTER_BYTES:
            # Small file: header read above already covers the whole file.
            return header

        handle.seek(max(size - _FOOTER_BYTES, 0))
        footer = handle.read(_FOOTER_BYTES)

    # Concatenating header+footer is sufficient for puremagic's signature
    # tables, which match against fixed byte offsets from the start or end
    # of a file, not the full file contents.
    return header + footer


class SignaturePolicy:
    def __init__(self, extension_policy: ExtensionPolicy, *, enabled: bool = True) -> None:
        self._extension_policy = extension_policy
        self._enabled = enabled

    def inspect_file(self, path: Path, *, claimed_extension: str) -> SignatureResult:
        if not self._enabled:
            return SignatureResult.allow_unknown()

        try:
            sample = _read_bounded_sample(path)
            matches = puremagic.magic_string(sample)
            if not matches:
                raise ValueError("no_signature_match")
            match = matches[0]
        except Exception:
            logger.debug("signature_unknown", extra={"path": str(path)})
            return SignatureResult.allow(
                detected_extension=None,
                mime_type=None,
                warnings=["signature_unknown"],
            )

        detected_extension = (match.extension or "").lower().strip() or None
        mime_type = match.mime_type or None
        normalized_claim = self._extension_policy.normalize_extension(claimed_extension)

        if detected_extension is None:
            return SignatureResult.allow(
                detected_extension=None,
                mime_type=mime_type,
                warnings=["signature_unknown"],
            )

        if self._extension_policy.is_blocked(detected_extension):
            return SignatureResult.reject(
                "blocked_signature_type",
                detected_extension=detected_extension,
                mime_type=mime_type,
            )

        detected_category = self._extension_policy.allowed_category_for_extension(detected_extension)
        claimed_category = self._extension_policy.allowed_category_for_extension(normalized_claim)

        if detected_category is None:
            return SignatureResult.reject(
                "unknown_signature_type",
                detected_extension=detected_extension,
                mime_type=mime_type,
            )

        warnings: list[str] = []
        if detected_extension != normalized_claim:
            if detected_category != claimed_category:
                return SignatureResult.reject(
                    "signature_category_mismatch",
                    detected_extension=detected_extension,
                    mime_type=mime_type,
                )
            warnings.append("signature_extension_mismatch")

        return SignatureResult.allow(
            detected_extension=detected_extension,
            mime_type=mime_type,
            warnings=warnings,
        )

        detected_extension = (match.extension or "").lower().strip() or None
        mime_type = match.mime_type or None
        normalized_claim = self._extension_policy.normalize_extension(claimed_extension)

        if detected_extension is None:
            return SignatureResult.allow(
                detected_extension=None,
                mime_type=mime_type,
                warnings=["signature_unknown"],
            )

        if self._extension_policy.is_blocked(detected_extension):
            return SignatureResult.reject(
                "blocked_signature_type",
                detected_extension=detected_extension,
                mime_type=mime_type,
            )

        detected_category = self._extension_policy.allowed_category_for_extension(detected_extension)
        claimed_category = self._extension_policy.allowed_category_for_extension(normalized_claim)

        if detected_category is None:
            return SignatureResult.reject(
                "unknown_signature_type",
                detected_extension=detected_extension,
                mime_type=mime_type,
            )

        warnings: list[str] = []
        if detected_extension != normalized_claim:
            if detected_category != claimed_category:
                return SignatureResult.reject(
                    "signature_category_mismatch",
                    detected_extension=detected_extension,
                    mime_type=mime_type,
                )
            warnings.append("signature_extension_mismatch")

        return SignatureResult.allow(
            detected_extension=detected_extension,
            mime_type=mime_type,
            warnings=warnings,
        )