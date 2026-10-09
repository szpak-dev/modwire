from ....shared.code.models.import_crossing_type import ImportCrossingType
from ....shared.code.models.source_export_kind import SourceExportKind
from ....shared.values.models.value_model import ValueModel


class ExportsReportItem(ValueModel):
    source_id: str
    name: str
    kind: SourceExportKind
    crossing_type: ImportCrossingType
    reason: str
