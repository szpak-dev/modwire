from ..base_test import ArchitectureTestCase


class ShapeTestCase(ArchitectureTestCase):
    def source_file(self, file_id: str) -> str:
        return "def example_function():\n    return 1\n"
