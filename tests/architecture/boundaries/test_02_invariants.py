from .base_test import BoundaryTestCase


class TestBoundaryInvariants(BoundaryTestCase):
    def test_preserves_shared_allow_exceptions_to_closed_module_rules(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [
                        {"name": "example-module", "match": "src/*"},
                        {"name": "example-shared", "match": "src/example_shared"},
                    ],
                    "rules": [
                        {
                            "source": "example-module",
                            "disallow": ["example-module"],
                            "allow": ["example-shared"],
                            "allow_same_match": True,
                        }
                    ],
                    "flow": {"module_tag": "example-module", "analyzers": ["module-boundaries"]},
                },
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            }
        )
        assert not self.violations(config, "src/example_a/example.source", "src/example_shared/example.source")
        assert self.violations(config, "src/example_a/example.source", "src/example_b/example.source")

    def test_cycle_analysis_evaluates_every_realm(self) -> None:
        config = self.application.configure(
            {
                "boundaries": {
                    "tags": [
                        {"name": "example-backend", "match": "example_backend/*"},
                        {"name": "example-frontend", "match": "example_frontend/*"},
                    ],
                    "flow": {
                        "realms": [
                            {"name": "example-backend", "module_tag": "example-backend"},
                            {"name": "example-frontend", "module_tag": "example-frontend"},
                        ],
                        "analyzers": ["no-cycles"],
                    },
                },
                "shape": {"realms": [{"name": "example-source", "match": "*"}]},
            }
        )
        paths = (
            "example_backend/example_a/example_backend_one.source",
            "example_backend/example_b/example_backend_two.source",
            "example_frontend/example_a/example_frontend_one.source",
            "example_frontend/example_b/example_frontend_two.source",
        )
        edges = tuple((paths[a], paths[b], "resolved", "example.target") for a, b in ((0, 1), (1, 0), (2, 3), (3, 2)))
        report = self.report("architecture.violations.flow", config, self.queryable_map(paths, edges))
        assert {item.rule_name for item in report.violations} == {
            "analyzer:example-backend:no-cycles",
            "analyzer:example-frontend:no-cycles",
        }
