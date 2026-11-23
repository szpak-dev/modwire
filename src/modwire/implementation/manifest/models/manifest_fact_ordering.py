import json
from dataclasses import dataclass
from functools import cached_property

from pydantic import SerializeAsAny, TypeAdapter
from wireup import injectable

from ....shared.code.models.callables.source_call import SourceCall
from ....shared.values.models.value_model import ValueModel


@injectable
@dataclass(frozen=True)
class ManifestFactOrdering:
    @cached_property
    def values(self) -> TypeAdapter[SerializeAsAny[ValueModel] | SourceCall]:
        return TypeAdapter(SerializeAsAny[ValueModel] | SourceCall)

    def key(self, value: ValueModel | SourceCall) -> str:
        document: object = self.values.dump_python(value, mode="json")
        return json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
