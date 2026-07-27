from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.models.resume import ResumeState
from app.state.atomic_json import read_json_file, write_json_atomic


@dataclass(slots=True)
class ResumeConsistencyResult:
    is_consistent: bool
    actual_part_size: int
    recorded_bytes_written: int
    reason: str | None = None


class ResumeStore:
    def load(self, state_path: Path) -> ResumeState:
        payload = read_json_file(state_path)
        return ResumeState.from_dict(payload)

    def save(self, state_path: Path, state: ResumeState) -> None:
        write_json_atomic(state_path, state.to_dict())

    def delete(self, state_path: Path) -> None:
        state_path.unlink(missing_ok=True)

    def part_file_path_for(self, final_path: Path) -> Path:
        return final_path.with_name(final_path.name + ".part")

    def state_file_path_for(self, final_path: Path) -> Path:
        return final_path.with_name(final_path.name + ".part.json")

    def check_consistency(self, part_path: Path, state_path: Path) -> ResumeConsistencyResult:
        if not state_path.exists():
            return ResumeConsistencyResult(
                is_consistent=False,
                actual_part_size=part_path.stat().st_size if part_path.exists() else 0,
                recorded_bytes_written=0,
                reason="missing_state_file",
            )

        if not part_path.exists():
            state = self.load(state_path)
            return ResumeConsistencyResult(
                is_consistent=False,
                actual_part_size=0,
                recorded_bytes_written=state.bytes_written,
                reason="missing_part_file",
            )

        state = self.load(state_path)
        actual_size = part_path.stat().st_size
        recorded_size = state.bytes_written

        if actual_size != recorded_size:
            return ResumeConsistencyResult(
                is_consistent=False,
                actual_part_size=actual_size,
                recorded_bytes_written=recorded_size,
                reason="size_mismatch",
            )

        if recorded_size > state.expected_size:
            return ResumeConsistencyResult(
                is_consistent=False,
                actual_part_size=actual_size,
                recorded_bytes_written=recorded_size,
                reason="recorded_size_exceeds_expected_size",
            )

        return ResumeConsistencyResult(
            is_consistent=True,
            actual_part_size=actual_size,
            recorded_bytes_written=recorded_size,
            reason=None,
        )