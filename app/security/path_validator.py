"""
Security module for validating file paths and preventing path traversal attacks.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class PathSecurityValidator:
    """
    Validates file paths to ensure they stay within designated boundaries.
    Prevents path traversal attacks and unauthorized file access.
    """

    def __init__(self, allowed_root: Path) -> None:
        """
        Initialize validator with the allowed root directory.

        Args:
            allowed_root: The root directory that all files must be within.

        Raises:
            ValueError: If allowed_root doesn't exist or is not a directory.
        """
        allowed_root = allowed_root.resolve()
        if not allowed_root.exists():
            raise ValueError(f"Allowed root does not exist: {allowed_root}")
        if not allowed_root.is_dir():
            raise ValueError(f"Allowed root is not a directory: {allowed_root}")
        self.allowed_root = allowed_root

    def validate_relative_path(self, relative_path: str | Path) -> Path:
        """
        Validate that a relative path is safe and resolve it within the allowed root.

        Args:
            relative_path: The relative path to validate.

        Returns:
            The safe, resolved absolute path.

        Raises:
            ValueError: If the path is invalid or tries to escape the root.
        """
        if isinstance(relative_path, str):
            relative_path = Path(relative_path)

        # Convert to POSIX-style to normalize separators
        path_str = str(relative_path).replace("\\", "/")

        # Check for null bytes
        if "\x00" in path_str:
            raise ValueError(f"Path contains null bytes: {relative_path}")

        # Check for invalid characters
        invalid_chars = ["<", ">", "|", "\x00", "\n", "\r"]
        for char in invalid_chars:
            if char in path_str:
                raise ValueError(f"Path contains invalid character: {char}")

        # Remove leading slashes to ensure relative path
        path_str = path_str.lstrip("/")

        # Reconstruct as Path object
        normalized_path = Path(path_str)

        # Resolve the path within the allowed root
        try:
            # Attempt to resolve symlinks safely
            full_path = (self.allowed_root / normalized_path).resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Cannot resolve path: {e}")

        # Verify the resolved path is still within the allowed root
        try:
            full_path.relative_to(self.allowed_root)
        except ValueError:
            raise ValueError(f"Path escapes allowed root: {relative_path}")

        return full_path

    def validate_for_source(self, file_path: Path) -> Path:
        """
        Validate a file path for reading (source file).

        Args:
            file_path: The file path to validate.

        Returns:
            The validated absolute path.

        Raises:
            ValueError: If the path is invalid or outside the allowed root.
            FileNotFoundError: If the file doesn't exist.
        """
        file_path = file_path.resolve()

        try:
            file_path.relative_to(self.allowed_root)
        except ValueError:
            raise ValueError(f"Source file outside allowed root: {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"Source file does not exist: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Source path is not a file: {file_path}")

        return file_path

    def validate_for_destination(self, relative_path: str | Path) -> Path:
        """
        Validate a destination path for writing.

        Args:
            relative_path: The relative destination path.

        Returns:
            The validated absolute destination path.

        Raises:
            ValueError: If the path is invalid or outside the allowed root.
        """
        full_path = self.validate_relative_path(relative_path)

        # Ensure parent directory is within allowed root
        try:
            full_path.parent.relative_to(self.allowed_root)
        except ValueError:
            raise ValueError(f"Destination parent directory outside allowed root")

        return full_path

    def validate_directory(self, dir_path: Path) -> Path:
        """
        Validate a directory path.

        Args:
            dir_path: The directory path to validate.

        Returns:
            The validated absolute directory path.

        Raises:
            ValueError: If the path is invalid or outside the allowed root.
            NotADirectoryError: If the path is not a directory.
        """
        dir_path = dir_path.resolve()

        try:
            dir_path.relative_to(self.allowed_root)
        except ValueError:
            raise ValueError(f"Directory outside allowed root: {dir_path}")

        if dir_path.exists() and not dir_path.is_dir():
            raise NotADirectoryError(f"Path exists but is not a directory: {dir_path}")

        return dir_path


def create_safe_destination_path(
    destination_root: Path, relative_path: str | Path
) -> Path:
    """
    Helper function to safely create a destination path.

    Args:
        destination_root: The root directory for all transfers.
        relative_path: The relative path within the root.

    Returns:
        The safe, validated destination path.

    Raises:
        ValueError: If the path would escape the root directory.
    """
    validator = PathSecurityValidator(destination_root)
    return validator.validate_for_destination(relative_path)


def is_path_within_root(path: Path, root: Path) -> bool:
    """
    Check if a path is within a root directory.

    Args:
        path: The path to check.
        root: The root directory.

    Returns:
        True if path is within root, False otherwise.
    """
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
