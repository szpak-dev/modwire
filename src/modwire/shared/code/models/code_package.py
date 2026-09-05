from typing import Self

from pydantic import model_validator

from modwire.shared.values.models.value_model import ValueModel


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
            raise KeyError(f"Code package has no file {path!r}") from error

    def merged(self, other: "CodePackage") -> "CodePackage":
        overlap = sorted(set(self.files).intersection(other.files))
        if overlap:
            raise ValueError("Code packages contain duplicate paths: " + ", ".join(overlap))
        return type(self)(files={**self.files, **other.files})

    def _validate_file_path(self, path: str) -> None:
        if not path:
            raise ValueError("Code package file path cannot be empty.")
        if "\\" in path:
            raise ValueError("Code package file path must use POSIX separators.")
        if path.startswith("/"):
            raise ValueError("Code package file path must be relative.")
        if path.endswith("/"):
            raise ValueError("Code package file path must point to a file.")
        parts = path.split("/")
        if any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Code package file path cannot contain empty, current, or parent segments.")
