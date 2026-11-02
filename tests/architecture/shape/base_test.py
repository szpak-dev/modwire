from ...support.code_map import CodeMapFactory
from ..base_test import ArchitectureTestCase


class ShapeTestCase(ArchitectureTestCase):
    def source_file(self, file_id: str) -> dict[str, object]:
        return {
            "functions": [
                CodeMapFactory().source_function(
                    "example_function", line_count=1, parameter_count=0, optional_parameter_count=0
                )
            ]
        }
