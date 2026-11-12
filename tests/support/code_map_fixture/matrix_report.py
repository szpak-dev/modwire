import hashlib

from modwire.application import CodeMap

from .claim_result import ClaimResult
from .conclusion import Conclusion
from .discrepancy import Discrepancy
from .fixture_model import FixtureModel
from .language_capability_matrix.oracle.documents.extraction_obligation import ExtractionObligation
from .language_capability_matrix.values.names.language_id import LanguageId
from .language_capability_matrix.values.names.scenario_id import ScenarioId


class ExtractionMatrixReport(FixtureModel):
    revision: str
    workspace_digest: str
    matrix_schema_version: int
    runtime_requirements: str
    obligations: dict[Conclusion, ExtractionObligation]
    results: dict[LanguageId, dict[ScenarioId, tuple[ClaimResult, ...]]]
    observations: dict[LanguageId, dict[ScenarioId, CodeMap]]
    equivalence_cases: frozenset[ScenarioId]
    reviewed_gaps: dict[str, str]

    @property
    def conforms(self) -> bool:
        return bool(self.results) and all(
            result.satisfied
            for scenarios in self.results.values()
            for results in scenarios.values()
            for result in results
        )

    @property
    def regression_passes(self) -> bool:
        used: set[str] = set()
        for language, scenarios in self.results.items():
            for case, results in scenarios.items():
                for result in results:
                    if result.satisfied:
                        continue
                    if set(result.discrepancies) & {
                        Discrepancy.FALSE_SUPPORT,
                        Discrepancy.FALSE_COMPLETENESS,
                        Discrepancy.UNASSESSED,
                        Discrepancy.INVALID_EVIDENCE,
                        Discrepancy.EXTRACTION_FAILURE,
                    }:
                        return False
                    key = f"{language.value}:{case.value}:{result.subject}"
                    digest = hashlib.sha256(result.model_dump_json().encode()).hexdigest()
                    if key not in self.reviewed_gaps or self.reviewed_gaps[key] != digest:
                        return False
                    used.add(key)
        return bool(self.results) and used == set(self.reviewed_gaps)

    def table(self) -> str:
        languages = tuple(self.obligations[Conclusion.SOURCE_INVENTORY].languages)
        rows = [
            "| Obligation | " + " | ".join(language.value for language in languages) + " |",
            "| --- | " + " | ".join("---" for _ in languages) + " |",
        ]
        for conclusion, obligation in self.obligations.items():
            cells: list[str] = []
            for language in languages:
                results = tuple(
                    result
                    for case, items in self.results[language].items()
                    if case not in self.equivalence_cases
                    for result in items
                    if conclusion in result.conclusions
                )
                failures = sorted({item.value for result in results for item in result.discrepancies})
                cells.append(
                    ", ".join(failures)
                    if failures
                    else ("pass (bounded)" if obligation.languages[language].applicable else "N/A")
                )
            rows.append("| " + " | ".join((conclusion.value, *cells)) + " |")
        rows.extend(
            (
                "",
                f"Conformance: {'PASS' if self.conforms else 'FAIL'}",
                f"Regression: {'PASS' if self.regression_passes else 'FAIL'}",
                "",
            )
        )
        for language, scenarios in self.results.items():
            for case, results in scenarios.items():
                for result in results:
                    if not result.satisfied:
                        failures = ", ".join(item.value for item in result.discrepancies)
                        rows.append(
                            f"- {language.value}/{case.value}: {result.subject}: "
                            f"{failures}; owner #{result.owner_issue}"
                        )
        return "\n".join(rows)
