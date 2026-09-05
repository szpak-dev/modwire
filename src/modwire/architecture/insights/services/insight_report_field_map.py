from dataclasses import dataclass

from wireup import injectable


@injectable()
@dataclass(frozen=True)
class InsightReportFieldMap:
    def field_for(self, reporter_name: str) -> str:
        if reporter_name == "unused-exports":
            return "exports"
        return reporter_name.replace("-", "_")
