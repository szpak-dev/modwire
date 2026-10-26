import re
from enum import Enum
from pathlib import PurePosixPath


class FixtureLanguageConvention(Enum):
    PYTHON = ("python", (".py",), "_", False)
    RUBY = ("ruby", (".rb",), "_", False)
    TYPESCRIPT = ("typescript", (".ts", ".tsx", ".js", ".jsx"), "-", False)
    PHP = ("php", (".php",), "", True)
    JAVA = ("java", (".java",), "", True)

    def __init__(
        self,
        language: str,
        suffixes: tuple[str, ...],
        separator: str,
        class_named_file: bool,
    ) -> None:
        self.language = language
        self.suffixes = suffixes
        self.suffix = suffixes[0]
        self.separator = separator
        self.class_named_file = class_named_file

    def source_path(self, canonical_source_id: str, declaration_name: str) -> str:
        canonical_path = PurePosixPath(canonical_source_id)
        stem = declaration_name if self.class_named_file else canonical_path.stem.replace("_", self.separator)
        return str(PurePosixPath(*canonical_path.parts[:-1], f"{stem}{self.suffix}"))

    def member_name(self, canonical_name: str) -> str:
        if self.separator == "_":
            return canonical_name
        first, *remaining = canonical_name.split("_")
        return first + "".join(part.title() for part in remaining)

    def accepts_source_path(self, relative_path: str) -> bool:
        path = PurePosixPath(relative_path)
        if path.suffix not in self.suffixes:
            return False
        if self.class_named_file:
            pattern = r"[A-Z][A-Za-z0-9]*"
        elif self.separator == "_":
            pattern = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*"
        else:
            pattern = r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*"
        return re.fullmatch(pattern, path.stem) is not None
