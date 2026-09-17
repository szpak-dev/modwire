from dataclasses import dataclass

from wireup import injectable

from modwire.application import ModwireApplication


@injectable
@dataclass(frozen=True)
class ExampleConsumer:
    application: ModwireApplication

    def report_ids(self) -> tuple[str, ...]:
        return tuple(item.id for item in self.application.catalog().reports)
