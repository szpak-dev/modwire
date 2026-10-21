import sys

from modwire.autowiring import run_extractor
from modwire.extraction.extractors.models.extractor_failure_document import ExtractorFailureDocument
from modwire.extraction.extractors.models.source_parse_error import SourceParseError

if __name__ == "__main__":
    try:
        raise SystemExit(run_extractor("python"))
    except SourceParseError as error:
        failure = ExtractorFailureDocument(
            code="source_parse",
            language=error.language,
            path=error.path,
            line=error.line,
            column=error.column,
            diagnostic=error.diagnostic,
        )
        print(f"modwire-error:{failure.model_dump_json()}", file=sys.stderr)
        raise SystemExit(1) from error
