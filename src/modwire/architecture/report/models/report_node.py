from typing import Any

from pydantic import Field, computed_field, model_serializer

from ....shared.values.models.value_model import ValueModel
from .report_descriptor import ReportDescriptor
from .report_metadata import ReportMetadata


class ReportNode(ValueModel):
    report_id: str
    report_title: str
    report_description: str = ""
    report_path: str = ""
    report_order: int = 100
    report_children: tuple[type["ReportNode"], ...] = Field(default=(), exclude=True)

    @computed_field
    @property
    def metadata(self) -> ReportMetadata:
        return ReportDescriptor(report_type=type(self)).metadata()

    @model_serializer(mode="wrap")
    def serialize_report_node(self, handler: Any) -> dict[str, Any]:
        payload = handler(self)
        for field_name in (
            "report_id",
            "report_title",
            "report_description",
            "report_path",
            "report_order",
            "report_children",
        ):
            payload.pop(field_name, None)
        return payload
