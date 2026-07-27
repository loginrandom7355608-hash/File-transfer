from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class DuplicateDecision:
    action: str
    target_path: Path


def resolve_duplicate_path(target_path: Path, policy: str) -> DuplicateDecision:
    if not target_path.exists():
        return DuplicateDecision(action="write", target_path=target_path)

    normalized_policy = policy.strip().lower()

    if normalized_policy == "fail":
        return DuplicateDecision(action="fail", target_path=target_path)

    if normalized_policy == "rename_incoming":
        candidate = target_path
        counter = 1
        while candidate.exists():
            candidate = target_path.with_name(f"{target_path.stem} ({counter}){target_path.suffix}")
            counter += 1
        return DuplicateDecision(action="write", target_path=candidate)

    if normalized_policy == "replace":
        return DuplicateDecision(action="replace", target_path=target_path)

    return DuplicateDecision(action="skip", target_path=target_path)