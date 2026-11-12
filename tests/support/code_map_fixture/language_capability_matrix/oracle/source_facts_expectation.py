from typing import Literal

from pydantic import Field

from modwire.application import FileId, ScanPolicy

from ...fixture_model import FixtureModel
from .scenario_kind import ScenarioKind
from .source_facts import SourceFactExpectation


class SourceFactsExpectation(FixtureModel):
    kind: Literal[ScenarioKind.SOURCE_FACTS]
    sources: dict[FileId, SourceFactExpectation] = Field(min_length=1)
    policy: ScanPolicy
