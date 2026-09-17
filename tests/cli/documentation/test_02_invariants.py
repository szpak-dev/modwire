import pytest

from ..base_test import CliTestCase


class TestDocumentationInvariants(CliTestCase):
    def test_check_reports_staleness_without_writing_then_accepts_generated_documentation(self) -> None:
        content = "Example prefix\n<!-- generated:public-api:start -->\nexample stale\n"
        content += "<!-- generated:public-api:end -->\nExample suffix\n"
        self.write_files({"example_readme.md": content})
        readme = self.workspace / "example_readme.md"
        assert self.application.generate_documentation(readme, True) == 1
        assert readme.read_text() == content
        assert self.application.generate_documentation(readme, False) == 0
        generated = readme.read_text()
        assert generated.startswith("Example prefix\n")
        assert generated.endswith("Example suffix\n")
        assert "modwire report --language <language>" in generated
        assert self.application.generate_documentation(readme, True) == 0
        assert self.application.generate_documentation(readme, False) == 0
        assert readme.read_text() == generated

    @pytest.mark.parametrize(
        "content",
        ("example no markers", "<!-- generated:public-api:start -->", "<!-- generated:public-api:end -->"),
    )
    def test_missing_markers_do_not_overwrite_documentation(self, content: str) -> None:
        self.write_files({"example_readme.md": content})
        readme = self.workspace / "example_readme.md"
        with pytest.raises(ValueError, match="Missing generated documentation markers"):
            self.application.generate_documentation(readme, False)
        assert readme.read_text() == content
