from typing import Annotated

from pydantic import AfterValidator, ConfigDict, Field

from ....extraction.extractors.models.parsed_source_file import ParsedSourceFile
from ....shared.code.models.callables.source_parameter import SourceParameter
from ....shared.code.models.declarations.declaration_identity import DeclarationIdentity
from ....shared.code.models.declarations.source_namespace_membership import SourceNamespaceMembership
from ....shared.code.models.declarations.source_no_namespace import SourceNoNamespace
from ....shared.code.models.declarations.source_placement import SourcePlacement
from ....shared.code.models.declarations.source_resolved_target import SourceResolvedTarget
from ....shared.code.models.declarations.source_unresolved_target import SourceUnresolvedTarget
from ....shared.code.models.inventories.inventory_coverage import InventoryCoverage
from ....shared.code.models.inventories.member_inventory_coverage import MemberInventoryCoverage
from ....shared.code.models.source_types.absent import SourceTypeAbsent
from ....shared.code.models.source_types.reference import SourceTypeReference
from ....shared.code.models.source_types.unsupported import SourceTypeUnsupported
from ....shared.code.models.sources.identity import FileId
from ....shared.code.models.values.source_assigned_value import SourceAssignedValue
from ....shared.values.models.value_model import ValueModel
from ....shared.values.models.value_table import ValueTable


class IndexedSourceRecord(ValueModel):
    model_config = ConfigDict(cache_strings="all")
    source_id: FileId
    texts: Annotated[list[str], AfterValidator(ValueTable[str]().retain)]
    identities: Annotated[list[DeclarationIdentity], AfterValidator(ValueTable[DeclarationIdentity]().retain)]
    targets: Annotated[
        list[Annotated[SourceResolvedTarget | SourceUnresolvedTarget, Field(discriminator="kind")]],
        AfterValidator(ValueTable[SourceResolvedTarget | SourceUnresolvedTarget]().retain),
    ]
    types: Annotated[
        list[
            Annotated[
                SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported,
                Field(union_mode="left_to_right"),
            ]
        ],
        AfterValidator(ValueTable[SourceTypeAbsent | SourceTypeReference | SourceTypeUnsupported]().retain),
    ]
    coverages: Annotated[list[InventoryCoverage], AfterValidator(ValueTable[InventoryCoverage]().retain)]
    member_inventories: Annotated[
        list[MemberInventoryCoverage], AfterValidator(ValueTable[MemberInventoryCoverage]().retain)
    ]
    namespaces: Annotated[
        list[Annotated[SourceNoNamespace | SourceNamespaceMembership, Field(discriminator="kind")]],
        AfterValidator(ValueTable[SourceNoNamespace | SourceNamespaceMembership]().retain),
    ]
    placements: Annotated[list[SourcePlacement], AfterValidator(ValueTable[SourcePlacement]().retain)]
    assignments: Annotated[list[SourceAssignedValue], AfterValidator(ValueTable[SourceAssignedValue]().retain)]
    parameters: Annotated[list[SourceParameter], AfterValidator(ValueTable[SourceParameter]().retain)]
    facts: ParsedSourceFile
