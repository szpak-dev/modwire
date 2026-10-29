from pathlib import Path

from modwire.application import ModwireApplication, ScanPolicy


def analyze_tutorial() -> tuple[int, int, int]:
    root = Path(__file__).parent / "tutorial"
    application = ModwireApplication.create()
    config = application.configure(
        {
            "boundaries": {
                "tags": [
                    {"name": "feature", "match": "src/backend/*/*"},
                    {"name": "application", "match": "src/backend/*/*/application"},
                    {"name": "domain", "match": "src/backend/*/*/domain"},
                ],
                "flow": {
                    "module_tag": "feature",
                    "layers": ["application", "domain"],
                    "analyzers": ["backward-flow"],
                },
            },
            "shape": {
                "realms": [
                    {
                        "name": "backend-source",
                        "match": "src/backend",
                        "shape": {"max_functions_per_file": 10},
                    }
                ]
            },
        }
    )
    policy = ScanPolicy(excluded_patterns=(".git/**", ".modwire/**"))
    code_map = application.generate_queryable_map("python", str(root), policy)
    reports = application.analyze(code_map, config)
    flow = next(report for report in reports if report.metadata.id == "architecture.violations.flow")
    return code_map.files().count(), code_map.tracked_dependency_edges().count(), len(flow.violations)


if __name__ == "__main__":
    assert analyze_tutorial() == (2, 1, 1)
