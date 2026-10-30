from modwire.application import CodeMap, FileId

from ...fixture_model import FixtureModel
from .identities import FixtureSourceIdentities
from .observation import PublicFactObservation
from .selectors.selector import ScenarioFactSelector


class FixtureFactReference(FixtureModel):
    selector: ScenarioFactSelector

    def __hash__(self) -> int:
        return hash(self.selector.root)

    def source_id(self) -> FileId:
        selector = self.selector.root
        if selector.kind == "parameter_list":
            return selector.callable.source_id
        return selector.source

    def read_expected(self, code_map: CodeMap) -> PublicFactObservation:
        return self.selector.root.read_expected(code_map)

    def read_actual(self, code_map: CodeMap, identities: FixtureSourceIdentities) -> PublicFactObservation:
        return self.selector.root.read_actual(code_map, identities)
