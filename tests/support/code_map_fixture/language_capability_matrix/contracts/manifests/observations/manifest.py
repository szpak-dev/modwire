from typing import Annotated

from pydantic import Field

from .....fixture_root_model import FixtureRootModel
from .attribute import ManifestAttributeObservation
from .call import ManifestCallObservation
from .callable import ManifestCallableObservation
from .declaration_relation import ManifestDeclarationRelationObservation
from .dependency import ManifestDependencyObservation
from .namespace import ManifestNamespaceObservation
from .parameter import ManifestParameterObservation
from .source import ManifestSourceObservation
from .symbol import ManifestSymbolObservation


class ManifestObservation(
    FixtureRootModel[
        Annotated[
            ManifestSourceObservation
            | ManifestNamespaceObservation
            | ManifestSymbolObservation
            | ManifestCallableObservation
            | ManifestParameterObservation
            | ManifestAttributeObservation
            | ManifestCallObservation
            | ManifestDeclarationRelationObservation
            | ManifestDependencyObservation,
            Field(discriminator="kind"),
        ]
    ]
):
    pass
