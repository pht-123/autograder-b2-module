from __future__ import annotations

from pathlib import Path

from modules.exception_module.errors import StorageError


class FileStorage:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir

    def build_code_path(
        self,
        assignment_id: str,
        question_id: str,
        student_user_id: str,
        submission_id: str,
        language: str,
    ) -> Path:
        # For this homework, only Python is required.
        ext = "py" if language.lower() == "python" else "txt"
        return (
            self.base_dir
            / assignment_id
            / question_id
            / student_user_id
            / f"{submission_id}.{ext}"
        )

    def save_code(self, path: Path, code: str) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
        except Exception as exc:
            raise StorageError(f"failed to persist code to {path}: {exc}") from exc
