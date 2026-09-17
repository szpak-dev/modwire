from ..base_test import ArchitectureTestCase


class BoundaryTestCase(ArchitectureTestCase):
    def violations(self, config, source: str, target: str) -> tuple[tuple[str, ...], ...]:
        code_map = self.queryable_map((source, target), ((source, target, "resolved", "example.target"),))
        report = self.report("architecture.violations.flow", config, code_map)
        return tuple(violation.path for violation in report.violations)
