from ....shared.values.models.value_model import ValueModel
from .manifest_annotation_role import ManifestAnnotationRole


class ManifestAnnotation(ValueModel):
    target_id: str
    role: ManifestAnnotationRole
    expression: str
