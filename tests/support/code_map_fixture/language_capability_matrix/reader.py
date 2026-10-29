from dataclasses import dataclass
from pathlib import Path

from pydantic_yaml import parse_yaml_file_as

from ..fixture_contract_error import FixtureContractError
from .document import LanguageCapabilityDocument
from .index import LanguageCapabilityIndex
from .matrix import LanguageCapabilityMatrix


@dataclass(frozen=True)
class LanguageCapabilityMatrixReader:
    def read(self, index_path: Path) -> LanguageCapabilityMatrix:
        index = parse_yaml_file_as(LanguageCapabilityIndex, index_path)
        document_paths = tuple(index_path.parent / path for path in index.languages.values())
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
        documents = tuple(parse_yaml_file_as(LanguageCapabilityDocument, path) for path in document_paths)
        return LanguageCapabilityMatrix(
            index=index,
            languages=dict(zip(index.languages, documents, strict=True)),
        )
