from dataclasses import dataclass


@dataclass(frozen=True)
class Project:
    language: str
    project_id: str
    owner: str
    repository: str
    revision: str
    source_root: str

    @property
    def label(self) -> str:
        return f"{self.language}/{self.project_id}"

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repository}"
