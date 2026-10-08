from ....shared.code.models.identity import FileId
from ....shared.values.models.value_model import ValueModel


class ExtractorBatchInput(ValueModel):
    paths: dict[FileId, str]
