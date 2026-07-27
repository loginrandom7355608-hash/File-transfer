from __future__ import annotations

from pathlib import Path

from app.integrity.hashing import sha256_file


def verify_file_sha256(path: Path, expected_sha256: str, chunk_size: int = 8 * 1024 * 1024) -> bool:
    actual = sha256_file(path, chunk_size=chunk_size)
    return actual.lower() == expected_sha256.lower()