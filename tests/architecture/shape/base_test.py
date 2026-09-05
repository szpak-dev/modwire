from tests.architecture.base_test import ArchitectureTestCase


class ShapeTestCase(ArchitectureTestCase):
    def source_file(self, file_id: str) -> dict[str, object]:
        return {
            **super().source_file(file_id),
            "functions": [{"name": "example_function", "visibility": "public", "visibility_intent": "public",
                           "line_count": 1, "declared_args": 0, "optional_args": 0}],
            "public_symbol_count": 1,
        }
