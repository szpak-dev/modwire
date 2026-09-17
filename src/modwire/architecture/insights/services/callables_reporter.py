from dataclasses import dataclass

from wireup import injectable

from ...map.models.architecture_map import ArchitectureMap
from ..domain import InsightReporterInterface
from ..models.callable_report_entry import CallableReportEntry
from ..models.callables_report import CallablesReport


@injectable(as_type=InsightReporterInterface, qualifier="callables")
@dataclass(frozen=True)
class CallablesReporter(InsightReporterInterface):
    @property
    def name(self) -> str:
        return "callables"

    @property
    def report_type(self) -> type[CallablesReport]:
        return CallablesReport

    def collect(self, architecture_map: ArchitectureMap) -> CallablesReport:
        calls_by_source: dict[str, list[str]] = {}
        callers_by_target: dict[str, list[str]] = {}
        for call_result in architecture_map.code_map.calls().all():
            call = call_result.item
            target = call.target_callable_id or call.expression
            calls_by_source.setdefault(call.source_callable_id, []).append(target)
            if call.target_callable_id:
                callers_by_target.setdefault(call.target_callable_id, []).append(call.source_callable_id)
        entries = tuple(
            CallableReportEntry(
                source_callable=callable_result.item.id,
                calls=tuple(sorted(set(calls_by_source.get(callable_result.item.id, ())))),
                callers=tuple(sorted(set(callers_by_target.get(callable_result.item.id, ())))),
            )
            for callable_result in sorted(
                architecture_map.code_map.callables().all(), key=lambda result: result.item.id
            )
        )
        return self.report_type(entries=entries)
