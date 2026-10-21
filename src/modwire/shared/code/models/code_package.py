from typing import Self

from pydantic import model_validator

from ...values.models.value_model import ValueModel
from .code_validation_error import CodeValidationError
from .code_violation import CodeViolation


class CodePackage(ValueModel):
    files: dict[str, str]

    @model_validator(mode="after")
    def validate_file_paths(self) -> Self:
        for path in self.files:
            self._validate_file_path(path)
        return self

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(self.files))

    def contents_for(self, path: str) -> str:
        self._validate_file_path(path)
        try:
            return self.files[path]
        except KeyError as error:
            raise CodeValidationError(CodeViolation.MISSING_PACKAGE_FILE, path) from error

    def merged(self, other: "CodePackage") -> "CodePackage":
        overlap = sorted(set(self.files).intersection(other.files))
        if overlap:
            raise CodeValidationError(CodeViolation.DUPLICATE_PACKAGE_PATH, ", ".join(overlap))
        return type(self)(files={**self.files, **other.files})

    def _validate_file_path(self, path: str) -> None:
        if not path:
            raise CodeValidationError(CodeViolation.EMPTY_PACKAGE_PATH, "empty path")
        if "\\" in path:
            raise CodeValidationError(CodeViolation.NON_POSIX_PACKAGE_PATH, path)
        if path.startswith("/"):
            raise CodeValidationError(CodeViolation.ABSOLUTE_PACKAGE_PATH, path)
        if path.endswith("/"):
            raise CodeValidationError(CodeViolation.DIRECTORY_PACKAGE_PATH, path)
        parts = path.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise CodeValidationError(CodeViolation.NON_NORMALIZED_PACKAGE_PATH, path)
