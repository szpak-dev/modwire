from ..support.service_test import ServiceTestCase
from .fixtures import example_consumer
from .fixtures.example_consumer import ExampleConsumer


class TestConsumerIntegration(ServiceTestCase):
    def test_a_callers_container_can_inject_the_application(self) -> None:
        consumer = self.consumer_service(ExampleConsumer, (example_consumer,))
        assert consumer.report_ids() == (
            "architecture.map",
            "architecture.violations.flow",
            "architecture.violations.shape",
            "architecture.insights",
        )

    def test_configuration_is_scoped_to_each_analysis_call(self) -> None:
        source = self.application.generate_queryable_map(
            "python",
            self.project({"src/example.py": "def example_function():\n    pass\n"}),
            (),
        )
        strict = self.application.configure({"shape": {"realms": [{"name": "example-source", "match": "src"}]}})
        permissive = self.application.configure(
            {"shape": {"realms": [{"name": "example-source", "match": "src", "shape": {"max_functions_per_file": 1}}]}}
        )
        strict_reports = self.application.analyze(source, strict)
        relaxed_reports = self.application.analyze(source, permissive)
        assert next(item for item in strict_reports if item.metadata.id == "architecture.violations.shape").violations
        assert not next(
            item for item in relaxed_reports if item.metadata.id == "architecture.violations.shape"
        ).violations
        assert self.application.analyze(source, strict) == strict_reports
