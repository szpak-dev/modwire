from collections.abc import Sequence
from dataclasses import dataclass

from wireup import injectable

from modwire.architecture.config.application import ConfigApplication
from modwire.architecture.config.models.shape_realm import ShapeRealm
from modwire.architecture.map.models.architecture_map import ArchitectureMap
from modwire.architecture.report.domain import ReportCollector
from modwire.architecture.shape.domain import ShapeResolverInterface
from modwire.architecture.shape.models.shape_realm_architecture_map import ShapeRealmArchitectureMap
from modwire.architecture.shape.models.shape_report import ShapeReport
from modwire.architecture.shape.models.shape_violation import ShapeViolation
from modwire.shared.code.domain import PathMatcher


@injectable(as_type=ReportCollector, qualifier="shape")
@dataclass(frozen=True)
class ShapeApplication(ReportCollector):
    config: ConfigApplication
    paths: PathMatcher
    resolvers: Sequence[ShapeResolverInterface]

    @property
    def report_type(self) -> type[ShapeReport]:
        return ShapeReport

    def collect(self, architecture_map: ArchitectureMap) -> ShapeReport:
        resolvers = sorted(self.resolvers, key=lambda resolver: resolver.name)
        resolver_names = tuple(resolver.name for resolver in resolvers)
        violations: list[ShapeViolation] = []
        for realm in self.config.shape.realms:
            realm_map = self.realm_map(architecture_map, realm)
            for resolver in resolvers:
                violations.extend(
                    violation.model_copy(update={"realm": realm.name})
                    for violation in resolver.resolve(realm_map, realm.shape)
                )
        return self.report_type(violations=tuple(violations), resolvers=resolver_names)

    def realm_map(self, architecture_map: ArchitectureMap, realm: ShapeRealm) -> ShapeRealmArchitectureMap:
        return ShapeRealmArchitectureMap(
            code_map=architecture_map.code_map,
            shape_realm_name=realm.name,
            shape_realm_source_ids=frozenset(
                source_id
                for source_id in architecture_map.code_map.source_ids()
                if self.matches(realm.match, source_id)
                and not any(self.matches(pattern, source_id) for pattern in realm.excluded_patterns)
            ),
        )

    def matches(self, pattern: str, source_id: str) -> bool:
        return self.paths.match(source_id, pattern, scope=True) is not None
