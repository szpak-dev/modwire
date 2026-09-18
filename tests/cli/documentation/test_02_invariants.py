from ..base_test import CliTestCase


class TestDocumentationInvariants(CliTestCase):
    def test_readme_is_generated_from_published_interface_docstrings(self) -> None:
        self.write_files({"example_readme.md": "example stale\n"})
        readme = self.workspace / "example_readme.md"
        assert self.application.generate_documentation(readme, True) == 1
        assert readme.read_text() == "example stale\n"
        assert self.application.generate_documentation(readme, False) == 0
        generated = readme.read_text()
        assert generated.startswith("# Modwire\n")
        assert "## `ModwireApplication`" in generated
        assert "Discover supported source languages beneath a root" in generated
        assert "## `ScanPolicy`" in generated
        assert "Caller-owned filesystem traversal policy" in generated
        assert self.application.generate_documentation(readme, True) == 0
        assert self.application.generate_documentation(readme, False) == 0
        assert readme.read_text() == generated
