from typing import Literal

from .....fixture_model import FixtureModel
from ....values.names.annotation_expression import AnnotationExpression
from ....values.names.qualified_name import QualifiedName


class AnnotationObservation(FixtureModel):
    kind: Literal["annotation"]
    owner: QualifiedName
    expression: AnnotationExpression
