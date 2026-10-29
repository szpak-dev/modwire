from dataclasses import dataclass
from pathlib import Path

from pydantic_yaml import parse_yaml_file_as

from modwire.application import CodeMap

from ..fixture_contract_error import FixtureContractError
from .contracts.coverage import LanguageContract
from .model import LanguageCapabilityBundle, LanguageCapabilityIndex, LanguageCapabilityMatrix
from .projections.model import ReferenceProjection


@dataclass(frozen=True)
class LanguageCapabilityMatrixReader:
    def read(self, index_path: Path) -> LanguageCapabilityMatrix:
        index = parse_yaml_file_as(LanguageCapabilityIndex, index_path)
        contract_paths = tuple(index_path.parent / pair.contract.value for pair in index.languages.values())
        projection_paths = tuple(
            index_path.parent / pair.reference_projection.value for pair in index.languages.values()
        )
        self.validate_document_directory(contract_paths)
        self.validate_document_directory(projection_paths)
        contracts = tuple(parse_yaml_file_as(LanguageContract, path) for path in contract_paths)
        projections = tuple(parse_yaml_file_as(ReferenceProjection, path) for path in projection_paths)
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
