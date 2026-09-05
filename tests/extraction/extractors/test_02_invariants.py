from ..base_test import ExtractionTestCase


class TestPythonInvariants(ExtractionTestCase):
    def test_empty_source_set_yields_an_empty_map(self) -> None:
        result = self.extract({})
        assert result.source_ids() == ()
        assert result.dependency_edges().count() == 0

    def test_preserves_class_function_and_optional_argument_shapes(self) -> None:
        result = self.extract(
            {
                "src/example.py": (
                    "class ExampleValue:\n"
                    "    def example_method(self, example_input: str = '') -> str:\n"
                    "        return example_input\n"
                    "def example_function(example_input: str) -> str:\n"
                    "    return example_input\n"
                )
            }
        )
        assert result.classes().first().item.name == "ExampleValue"
        assert result.functions().first().item.name == "example_function"
        example_method = (
            result.callables().where_equal(lambda item: item.item.qualified_name, "ExampleValue.example_method").first()
        )
        assert example_method.item.optional_args == 1

    def test_repeated_extraction_is_deterministic(self) -> None:
        source = {"src/example.py": "class ExampleValue:\n    pass\n"}
        assert self.extract(source).code_map.to_dict() == self.extract(source).code_map.to_dict()
