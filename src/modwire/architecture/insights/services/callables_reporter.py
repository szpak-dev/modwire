from collections.abc import Mapping
from dataclasses import dataclass

from wireup import injectable

from ....shared.code.models.source_callable import SourceCallable
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
            source_id = call.source_callable_id.canonical()
            target_id = call.target_callable_id.canonical() if call.target_callable_id is not None else None
            target = target_id or call.expression
            if source_id not in calls_by_source:
                calls_by_source[source_id] = []
            calls_by_source[source_id].append(target)
            if target_id is not None:
                if target_id not in callers_by_target:
                    callers_by_target[target_id] = []
                callers_by_target[target_id].append(source_id)
        entries = tuple(
            self.entry(callable_result.item, calls_by_source, callers_by_target)
            for callable_result in sorted(
                architecture_map.code_map.callables().all(),
                key=lambda result: result.item.declaration_id.canonical(),
            )
        )
        return self.report_type(entries=entries)

    def entry(
        self,
        source_callable: SourceCallable,
        calls_by_source: Mapping[str, list[str]],
        callers_by_target: Mapping[str, list[str]],
    ) -> CallableReportEntry:
        source_id = source_callable.declaration_id.canonical()
        calls = () if source_id not in calls_by_source else tuple(sorted(set(calls_by_source[source_id])))
        callers = () if source_id not in callers_by_target else tuple(sorted(set(callers_by_target[source_id])))
        return CallableReportEntry(source_callable=source_id, calls=calls, callers=callers)
