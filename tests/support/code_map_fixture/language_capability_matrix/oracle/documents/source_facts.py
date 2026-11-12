from typing import Literal

from pydantic import Field

from modwire.application import FileId, ScanPolicy

from ....fixture_model import FixtureModel
from ...values.paths.document_path import RepositoryDocumentPath
from ..scenario_kind import ScenarioKind


class ScenarioSourceFactsDocument(FixtureModel):
    kind: Literal[ScenarioKind.SOURCE_FACTS]
    sources: dict[FileId, RepositoryDocumentPath] = Field(min_length=1)
    policy: ScanPolicy
