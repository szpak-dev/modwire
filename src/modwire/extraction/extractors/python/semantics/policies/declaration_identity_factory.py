from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ......shared.code.models.sources.identity import FileId


class PythonDeclarationIdentityFactory(ABC):
    @abstractmethod
    def create(
        self,
        source_id: FileId,
        family: DeclarationFamily,
        qualified_name: str,
        line: int,
        column: int,
    ) -> DeclarationIdentity:
        raise NotImplementedError


@injectable(as_type=PythonDeclarationIdentityFactory)
@dataclass(frozen=True)
class SourceDeclarationIdentityFactory(PythonDeclarationIdentityFactory):
    def create(
        self,
        source_id: FileId,
        family: DeclarationFamily,
        qualified_name: str,
        line: int,
        column: int,
    ) -> DeclarationIdentity:
        return DeclarationIdentity(
            source_id=source_id,
            family=family,
            qualified_name=qualified_name,
            ordinal=(line << 32) + column + 1,
        )
