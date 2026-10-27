import re
from pathlib import PurePosixPath

from .model import FixtureModel


class FixtureLanguageConvention(FixtureModel):
    suffix: str
    suffixes: tuple[str, ...]
    separator: str
    class_named_file: bool

    def source_path(self, canonical_source_id: str, declaration_name: str) -> str:
        path = PurePosixPath(canonical_source_id)
        stem = declaration_name if self.class_named_file else self.member_name(path.name)
        return str(PurePosixPath(*path.parts[:-1], f"{stem}{self.suffix}"))

    def member_name(self, canonical_name: str) -> str:
        separated = re.sub("([A-Z]+)([A-Z][a-z])", rf"\1{self.separator}\2", canonical_name)
        normalized = re.sub("([a-z0-9])([A-Z])", rf"\1{self.separator}\2", separated)
        return normalized.replace("_", self.separator).lower()

    def accepts_source_path(self, relative_path: str) -> bool:
        return PurePosixPath(relative_path).suffix in self.suffixes
