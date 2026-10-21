from modwire.application import SourceCallResolution

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

    def test_duplicate_callable_names_preserve_exact_call_ownership(self) -> None:
        result = self.extract(
            {
                "src/example.py": (
                    "def example_target():\n    return 1\n\n"
                    "def example_duplicate():\n    return example_target()\n\n"
                    "def example_duplicate():\n    return example_target()\n"
                )
            }
        )

        calls = tuple(item.item for item in result.calls().all())
        assert len(calls) == 2
        assert len({item.source_callable_id.canonical() for item in calls}) == 2
        assert all(item.target_callable_id is not None for item in calls)
        assert {item.target_callable_id.canonical() for item in calls if item.target_callable_id is not None} == {
            next(
                item.item.declaration_id.canonical()
                for item in result.callables().all()
                if item.item.qualified_name == "example_target"
            )
        }

    def test_ambiguous_callable_target_is_not_silently_overwritten(self) -> None:
        result = self.extract(
            {
                "src/example.py": (
                    "def example_duplicate():\n    return 1\n\n"
                    "def example_duplicate():\n    return 2\n\n"
                    "def example_caller():\n    return example_duplicate()\n"
                )
            }
        )

        call = result.calls().first().item
        assert call.resolution is SourceCallResolution.UNRESOLVED
        assert call.target_callable_id is None
