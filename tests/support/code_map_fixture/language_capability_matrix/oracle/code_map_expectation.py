from typing import Literal

from modwire.application import CodeMap

from ...fixture_model import FixtureModel
from .scenario_kind import ScenarioKind


class CodeMapExpectation(FixtureModel):
    kind: Literal[ScenarioKind.CODE_MAP]
    code_map: CodeMap
