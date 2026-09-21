from ..base_test import ArchitectureTestCase


class BoundaryTestCase(ArchitectureTestCase):
    def violations(self, config, source: str, target: str) -> tuple[tuple[str, ...], ...]:
        code_map = self.queryable_map((source, target), ((source, target, "resolved", "example.target"),))
        report = self.report("architecture.violations.flow", config, code_map)
        return tuple(violation.path for violation in report.violations)

    def public_api_configuration(self):
        return self.application.configure(
            {
                "boundaries": {
                    "tags": [
                        {"name": "context", "match": "src/modwire/*", "excluded_patterns": ["src/modwire/*.py"]},
                        {
                            "name": "module",
                            "match": "src/modwire/*/*",
                            "excluded_patterns": ["src/modwire/*/*.py"],
                        },
                        {"name": "facade", "match": "src/modwire/*/facade.py"},
                        {"name": "application", "match": "src/modwire/*/*/application.py"},
                        {"name": "model", "match": "src/modwire/*/*/models"},
                        {"name": "service", "match": "src/modwire/*/*/services"},
                        {"name": "shared", "match": "src/modwire/shared"},
                        {"name": "public-application", "match": "src/modwire/application.py"},
                        {"name": "autowiring", "match": "src/modwire/autowiring.py"},
                        {"name": "tests", "match": "tests"},
                    ],
                    "rules": [{"realm": "test-api", "source": "tests", "allow": ["public-application"]}],
                    "flow": {
                        "realms": [{"name": "test-api", "module_tag": "tests"}],
                        "analyzers": ["module-boundaries"],
                    },
                },
                "shape": {"realms": [{"name": "example-source", "match": "*"}]},
            }
        )
