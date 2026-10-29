import json
import sys
from dataclasses import dataclass

from modwire.application import (
    ExtractorContractError,
    ExtractorUnavailableError,
    ModwireApplication,
    ScanPolicy,
)


@dataclass(frozen=True)
class FailureConsumer:
    def run(self, root: str, language: str) -> int:
        application = ModwireApplication.create()
        try:
            application.generate_map(language, root, ScanPolicy())
        except ExtractorUnavailableError as error:
            print(
                json.dumps(
                    {
                        "executable": error.executable,
                        "language": error.language,
                        "type": "ExtractorUnavailableError",
                    },
                    sort_keys=True,
                )
            )
        except ExtractorContractError as error:
            cause = error.__cause__
            print(
                json.dumps(
                    {
                        "cause": cause.__class__.__name__ if cause is not None else "",
                        "diagnostic": error.diagnostic,
                        "duplicate_source_ids": tuple(map(str, error.duplicate_source_ids)),
                        "language": error.language,
                        "missing_source_ids": tuple(map(str, error.missing_source_ids)),
                        "type": "ExtractorContractError",
                        "unexpected_source_ids": tuple(map(str, error.unexpected_source_ids)),
                        "violation": error.violation.value,
                    },
                    sort_keys=True,
                )
            )
        else:
            print(json.dumps({"type": "success"}, sort_keys=True))
        return 0


raise SystemExit(FailureConsumer().run(sys.argv[1], sys.argv[2]))
