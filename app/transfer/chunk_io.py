from __future__ import annotations

from pathlib import Path
from typing import BinaryIO, Iterator


def iter_file_chunks(path: Path, *, start_offset: int = 0, chunk_size: int = 8 * 1024 * 1024) -> Iterator[bytes]:
    with path.open("rb") as handle:
        handle.seek(start_offset)
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            yield chunk


def write_chunks(handle: BinaryIO, chunks: Iterator[bytes]) -> int:
    total_written = 0
    for chunk in chunks:
        handle.write(chunk)
        total_written += len(chunk)
    return total_written