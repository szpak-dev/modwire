import json
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as

from modwire.application import CodeMap

from ..fixture_contract_error import FixtureContractError
from .bundle import LanguageCapabilityBundle
from .contracts.coverage.contract import LanguageContract
from .documents.index import LanguageCapabilityIndex
from .documents.yaml_document import YamlDocument
from .matrix import LanguageCapabilityMatrix
from .projections.reference_projection import ReferenceProjection


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
        bundles = tuple(
            LanguageCapabilityBundle(contract=contract, reference_projection=projection)
            for contract, projection in zip(contracts, projections, strict=True)
        )
        reference_path = index_path.parent / index.reference_code_map.value
        reference_code_map = CodeMap.model_validate_json(reference_path.read_text(encoding="utf-8"))
        return LanguageCapabilityMatrix(
            index=index,
            reference_code_map=reference_code_map,
            languages=dict(zip(index.languages, bundles, strict=True)),
        )

    def read_document[Document: BaseModel](self, path: Path, model: type[Document]) -> Document:
        document = parse_yaml_raw_as(YamlDocument, path.read_text(encoding="utf-8"))
        return model.model_validate_json(json.dumps(document.root), strict=True)

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
