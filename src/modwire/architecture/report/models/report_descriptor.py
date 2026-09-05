from pydantic import BaseModel

from ....shared.values.models.value_model import ValueModel
from .report_metadata import ReportMetadata


class ReportDescriptor(ValueModel):
    report_type: type[BaseModel]

    def metadata(self) -> ReportMetadata:
        fields = self.report_type.model_fields
        children = tuple(
            sorted(
                (ReportDescriptor(report_type=child).metadata() for child in fields["report_children"].default),
                key=lambda child: (child.order, child.id),
            )
        )
        return ReportMetadata(
            id=fields["report_id"].default,
            title=fields["report_title"].default,
            description=fields["report_description"].default,
            model=f"{self.report_type.__module__}.{self.report_type.__qualname__}",
            path=fields["report_path"].default or fields["report_id"].default,
            order=fields["report_order"].default,
            children=children,
        )
