from ...support.code_map import CodeMapFactory
from ..base_test import ArchitectureTestCase


class ShapeTestCase(ArchitectureTestCase):
    def source_file(self, file_id: str) -> dict[str, object]:
        return {"functions": [CodeMapFactory.symbol("example_function")]}
