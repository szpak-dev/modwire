import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as

from modwire.application import CodeMap, FileId, SourceExtraction, SourceFile

from ..fixture_contract_error import FixtureContractError
from ..scenario_contract_error import ScenarioContractError
from ..scenario_violation import ScenarioViolation
from .bundle import LanguageCapabilityBundle
from .contracts.coverage.contract import LanguageContract
from .documents.index import LanguageCapabilityIndex
from .documents.yaml_document import YamlDocument
from .matrix import LanguageCapabilityMatrix
from .oracle.binder import FixtureScenarioBinder
from .oracle.catalog import FixtureScenarioCatalog
from .oracle.code_map_expectation import CodeMapExpectation
from .oracle.documents.catalog import ScenarioCatalogDocument
from .oracle.documents.scenario import ScenarioDocument
from .oracle.expected_scenario import ExpectedScenario
from .oracle.scenario_kind import ScenarioKind
from .oracle.source_facts import SourceFactExpectation
from .oracle.source_facts_expectation import SourceFactsExpectation
from .projections.reference_projection import ReferenceProjection
from .values.names.identifier import Identifier
from .values.names.scenario_id import ScenarioId
from .values.paths.document_path import RepositoryDocumentPath


@dataclass(frozen=True)
class LanguageCapabilityMatrixReader:
    def read(self, index_path: Path) -> LanguageCapabilityMatrix:
        index = self.read_document(index_path, LanguageCapabilityIndex)
        contract_paths = tuple(index_path.parent / pair.contract.value for pair in index.languages.values())
        projection_paths = tuple(
            index_path.parent / pair.reference_projection.value for pair in index.languages.values()
        )
        self.validate_document_directory(contract_paths)
        self.validate_document_directory(projection_paths)
        contracts = tuple(self.read_document(path, LanguageContract) for path in contract_paths)
        projections = tuple(self.read_document(path, ReferenceProjection) for path in projection_paths)
        catalog = self.read_catalog(index_path, index)
        binder = FixtureScenarioBinder(catalog, index.reference_scenario)
        bundles = tuple(
            LanguageCapabilityBundle(
                contract=contract,
                reference_projection=projection,
                scenarios=(
                    binder.bind_reference(projection),
                    *(binder.bind_document(contract, document) for document in projection.scenarios),
                ),
            )
            for contract, projection in zip(contracts, projections, strict=True)
        )
        return LanguageCapabilityMatrix(
            index=index,
            catalog=catalog,
            languages=dict(zip(index.languages, bundles, strict=True)),
        )

    def read_catalog(self, index_path: Path, index: LanguageCapabilityIndex) -> FixtureScenarioCatalog:
        repository = index_path.parent
        catalog_path = repository / index.scenario_catalog.value
        document = self.read_document(catalog_path, ScenarioCatalogDocument)
        paths = {catalog_path}
        expected: dict[ScenarioId, ExpectedScenario] = {}
        source_documents: dict[ScenarioId, dict[FileId, RepositoryDocumentPath]] = {}
        producers: set[Identifier] = set()
        for name, path in document.scenarios.items():
            scenario_path = repository / path.value
            paths.add(scenario_path)
            scenario = self.read_document(scenario_path, ScenarioDocument).root
            if scenario.kind is ScenarioKind.SOURCE_FACTS:
                source_documents[name] = scenario.sources
                sources = {
                    source: self.read_json_document(repository / source_path.value, SourceFactExpectation)
                    for source, source_path in scenario.sources.items()
                }
                paths.update(repository / path.value for path in scenario.sources.values())
                expected[name] = ExpectedScenario(
                    SourceFactsExpectation(kind=ScenarioKind.SOURCE_FACTS, sources=sources, policy=scenario.policy)
                )
                continue
            if scenario.producer not in document.producers:
                raise ScenarioContractError(ScenarioViolation.UNKNOWN_PRODUCER, name.value)
            producers.add(scenario.producer)
            source_documents[name] = scenario.extraction.files
            files = {
                source: self.read_json_document(repository / source_path.value, SourceFile)
                for source, source_path in scenario.extraction.files.items()
            }
            paths.update(repository / path.value for path in scenario.extraction.files.values())
            producer = document.producers[scenario.producer]
            code_map = CodeMap(
                language=producer.extractor.language,
                producer=producer,
                extraction=SourceExtraction(
                    files=files,
                    import_identities={source.import_identity: file_id for file_id, source in files.items()},
                    manifest=scenario.extraction.manifest,
                    files_found=len(files),
                    files_excluded=scenario.extraction.files_excluded,
                    directories_pruned=scenario.extraction.directories_pruned,
                ),
                dependency_graph=scenario.dependency_graph,
            )
            expected[name] = ExpectedScenario(CodeMapExpectation(kind=ScenarioKind.CODE_MAP, code_map=code_map))
        self.validate_catalog_inventory(catalog_path.parent, paths)
        if producers != set(document.producers):
            raise ScenarioContractError(ScenarioViolation.UNUSED_PRODUCER, str(catalog_path))
        return FixtureScenarioCatalog(
            expected=expected,
            source_documents=source_documents,
            obligations=document.obligations,
            model_gaps=document.model_gaps,
            reviewed_gaps=document.reviewed_gaps,
        )

    def validate_catalog_inventory(self, root: Path, paths: set[Path]) -> None:
        if any(not path.is_relative_to(root) for path in paths):
            raise FixtureContractError("scenario documents must stay inside the declared catalog directory")
        expected = paths | {
            parent for path in paths for parent in path.parents if parent != root and parent.is_relative_to(root)
        }
        actual = set(root.rglob("*"))
        if actual != expected:
            raise FixtureContractError("scenario document inventory differs from the complete typed catalog")

    def read_document[Document: BaseModel](self, path: Path, model: type[Document]) -> Document:
        document = parse_yaml_raw_as(YamlDocument, self.document_text(path))
        return model.model_validate_json(json.dumps(document.root), strict=True)

    def read_json_document[Document: BaseModel](self, path: Path, model: type[Document]) -> Document:
        text = self.document_text(path)
        json.loads(text, object_pairs_hook=self.unique_json_object)
        return model.model_validate_json(text, strict=True)

    def unique_json_object(self, pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for name, value in pairs:
            if name in result:
                raise FixtureContractError(f"duplicate JSON object field: {name}")
            result[name] = value
        return result

    def document_text(self, path: Path) -> str:
        if not path.is_file():
            raise FixtureContractError(f"declared document is missing or is not a file: {path}")
        return path.read_text(encoding="utf-8")

    def validate_document_directory(self, document_paths: tuple[Path, ...]) -> None:
        document_root = document_paths[0].parent
        expected_inventory = tuple(sorted(path.name for path in document_paths))
        if not document_root.is_dir():
            raise FixtureContractError(f"language document directory is missing: {document_root}")
        actual_entries = tuple(sorted(document_root.iterdir()))
        actual_inventory = tuple(path.name for path in actual_entries)
        if actual_inventory != expected_inventory or any(not path.is_file() for path in actual_entries):
            raise FixtureContractError(
                f"language document inventory mismatch: expected {expected_inventory}, got {actual_inventory}"
            )
