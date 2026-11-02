import json
import runpy
import shutil

from ..cli.base_test import CliTestCase


class TestDocumentationExamples(CliTestCase):
    examples = CliTestCase.repository / "docs/_examples"

    def copy_tutorial(self) -> None:
        shutil.copytree(self.examples / "tutorial", self.workspace, dirs_exist_ok=True)

    def test_tutorial_exposes_and_repairs_the_documented_backward_dependency(self) -> None:
        self.copy_tutorial()

        failed = self.run_cli(("report", "--language", "python", "--summary", "--no-cache"))

        assert failed.returncode == 1
        assert "[analyzer:backend:backward-flow]" in failed.stdout
        assert "src/backend/sales/orders/domain/tax.py" in failed.stdout
        assert "points backward to" in failed.stdout
        assert "src/backend/sales/orders/application/totals.py" in failed.stdout

        repair = (self.examples / "tutorial-repair/tax.py").read_text(encoding="utf-8")
        (self.workspace / "src/backend/sales/orders/domain/tax.py").write_text(repair, encoding="utf-8")
        repaired = self.run_cli(("report", "--language", "python", "--summary", "--no-cache"))

        assert repaired.returncode == 0, repaired.stderr
        assert "Architecture checks passed." in repaired.stdout

    def test_tutorial_typescript_source_passes_the_shared_configuration(self) -> None:
        self.copy_tutorial()

        result = self.run_cli(("report", "--language", "typescript", "--summary", "--no-cache"))

        assert result.returncode == 0, result.stderr
        assert "Architecture checks passed." in result.stdout

    def test_python_api_example_runs_through_the_public_application(self) -> None:
        runpy.run_path(str(self.examples / "python_api.py"), run_name="__main__")

    def test_language_support_links_the_root_matrix_without_copying_status_cells(self) -> None:
        page = (self.repository / "docs/reference/language-support.md").read_text(encoding="utf-8")

        assert "[`language-capabilities.yaml`](../../language-capabilities.yaml)" in page
        assert "| Capability |" not in page
        assert "| Family | Required fact evidence |" not in page

    def test_recorded_evidence_page_tracks_authoritative_json(self) -> None:
        page = (self.repository / "docs/reference/evidence.md").read_text(encoding="utf-8")
        extraction = self.load_json("tests/extraction/big_projects/results.json")
        benchmark = self.load_json("tests/extraction/scan_benchmark/results.json")
        files = sum(project["files_built"] for project in extraction["projects"].values())

        assert extraction["implementation_revision"] in page
        assert f"{files:,}" in page
        assert str(extraction["total_seconds"]) in page
        assert benchmark["baseline_revision"] in page
        assert benchmark["pruned_implementation_revision"] in page
        assert str(benchmark["baseline"]["median_seconds"]) in page
        assert str(benchmark["pruned"]["median_seconds"]) in page
        assert f"{benchmark['speedup']}x" in page
        assert f"{benchmark['reduction_percent']}%" in page

    def test_canonical_slogan_has_one_product_entrance(self) -> None:
        slogan = "Polyglot architecture checks, one model."
        entrances = (
            self.repository / "README.md",
            self.repository / "docs/index.md",
            self.repository / "pyproject.toml",
        )

        assert sum(path.read_text(encoding="utf-8").count(slogan) for path in entrances) == 1

    def load_json(self, relative: str) -> dict[str, object]:
        path = self.repository / relative
        return json.loads(path.read_text(encoding="utf-8"))
