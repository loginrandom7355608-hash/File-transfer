from __future__ import annotations

from pathlib import Path

from app.models.resume import ResumeState
from app.state.resume_store import ResumeStore


def build_state() -> ResumeState:
    return ResumeState(
        state_version=1,
        session_id="session-1",
        transfer_id="transfer-1",
        relative_path="videos/movie.mkv",
        original_filename="movie.mkv",
        expected_size=1000,
        bytes_written=400,
        chunk_size=1024,
        source_size=1000,
        source_mtime_ns=123456789,
        expected_sha256="abc123",
        status="in_progress",
        retry_count=0,
        started_at="2026-07-24T11:00:00Z",
        updated_at="2026-07-24T11:05:00Z",
    )


def test_resume_store_save_and_load(tmp_path: Path) -> None:
    store = ResumeStore()
    state_path = tmp_path / "movie.mkv.part.json"
    state = build_state()

    store.save(state_path, state)
    loaded = store.load(state_path)

    assert loaded == state


def test_resume_store_consistency_ok(tmp_path: Path) -> None:
    store = ResumeStore()
    final_path = tmp_path / "movie.mkv"
    part_path = store.part_file_path_for(final_path)
    state_path = store.state_file_path_for(final_path)

    part_path.write_bytes(b"x" * 400)
    state = build_state()
    store.save(state_path, state)

    result = store.check_consistency(part_path, state_path)

    assert result.is_consistent is True
    assert result.actual_part_size == 400
    assert result.recorded_bytes_written == 400
    assert result.reason is None


def test_resume_store_consistency_missing_state(tmp_path: Path) -> None:
    store = ResumeStore()
    part_path = tmp_path / "movie.mkv.part"
    state_path = tmp_path / "movie.mkv.part.json"

    part_path.write_bytes(b"x" * 100)

    result = store.check_consistency(part_path, state_path)

    assert result.is_consistent is False
    assert result.reason == "missing_state_file"


def test_resume_store_consistency_missing_part(tmp_path: Path) -> None:
    store = ResumeStore()
    final_path = tmp_path / "movie.mkv"
    part_path = store.part_file_path_for(final_path)
    state_path = store.state_file_path_for(final_path)

    store.save(state_path, build_state())

    result = store.check_consistency(part_path, state_path)

    assert result.is_consistent is False
    assert result.reason == "missing_part_file"


def test_resume_store_consistency_size_mismatch(tmp_path: Path) -> None:
    store = ResumeStore()
    final_path = tmp_path / "movie.mkv"
    part_path = store.part_file_path_for(final_path)
    state_path = store.state_file_path_for(final_path)

    part_path.write_bytes(b"x" * 350)
    store.save(state_path, build_state())

    result = store.check_consistency(part_path, state_path)

    assert result.is_consistent is False
    assert result.reason == "size_mismatch"


def test_resume_store_consistency_recorded_exceeds_expected(tmp_path: Path) -> None:
    store = ResumeStore()
    final_path = tmp_path / "movie.mkv"
    part_path = store.part_file_path_for(final_path)
    state_path = store.state_file_path_for(final_path)

    state = build_state()
    state = ResumeState(
        state_version=state.state_version,
        session_id=state.session_id,
        transfer_id=state.transfer_id,
        relative_path=state.relative_path,
        original_filename=state.original_filename,
        expected_size=300,
        bytes_written=400,
        chunk_size=state.chunk_size,
        source_size=state.source_size,
        source_mtime_ns=state.source_mtime_ns,
        expected_sha256=state.expected_sha256,
        status=state.status,
        retry_count=state.retry_count,
        started_at=state.started_at,
        updated_at=state.updated_at,
    )

    part_path.write_bytes(b"x" * 400)
    store.save(state_path, state)

    result = store.check_consistency(part_path, state_path)

    assert result.is_consistent is False
    assert result.reason == "recorded_size_exceeds_expected_size"