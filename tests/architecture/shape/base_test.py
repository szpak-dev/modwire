from ...support.code_map import CodeMapFactory
from ..base_test import ArchitectureTestCase


class ShapeTestCase(ArchitectureTestCase):
    def source_file(self, file_id: str) -> dict[str, object]:
        return {
            "functions": [CodeMapFactory().symbol("example_function", line_count=1, declared_args=0, optional_args=0)]
        }
