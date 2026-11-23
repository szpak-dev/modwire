import sys

from .....autowiring import run_extractor
from .....shared.failures.models.modwire_error_code import ModwireErrorCode
from ...models.extractor_failure_document import ExtractorFailureDocument
from ...models.source_parse_error import SourceParseError

if __name__ == "__main__":
    try:
        raise SystemExit(run_extractor("python"))
    except SourceParseError as error:
        print(
            "modwire-error:"
            + ExtractorFailureDocument(
                code=ModwireErrorCode.SOURCE_PARSE,
                language=error.language,
                path=error.path,
                line=error.line,
                column=error.column,
                diagnostic=error.diagnostic,
            ).model_dump_json(),
            file=sys.stderr,
        )
        raise SystemExit(1) from error
