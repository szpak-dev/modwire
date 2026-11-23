from abc import ABC, abstractmethod
from dataclasses import dataclass

from wireup import injectable

from ......shared.code.models.declarations.declaration_family import DeclarationFamily
from ......shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ...observations.source_context import PythonSourceContext


class PythonDeclarationIdentityFactory(ABC):
    @abstractmethod
    def create(
        self,
        context: PythonSourceContext,
        family: DeclarationFamily,
        qualified_name: str,
        ordinal: int,
    ) -> DeclarationIdentity:
        raise NotImplementedError


@injectable(as_type=PythonDeclarationIdentityFactory)
@dataclass(frozen=True)
class SourceDeclarationIdentityFactory(PythonDeclarationIdentityFactory):
    def create(
        self,
        context: PythonSourceContext,
        family: DeclarationFamily,
        qualified_name: str,
        ordinal: int,
    ) -> DeclarationIdentity:
        return DeclarationIdentity(
            source_id=context.source_id,
            family=family,
            qualified_name=qualified_name,
            ordinal=ordinal,
            content_digest=context.content_digest,
        )
