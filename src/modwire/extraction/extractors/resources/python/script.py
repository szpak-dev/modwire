import json
import sys

from modwire.autowiring import run_extractor
from modwire.extraction.extractors.models.source_parse_error import SourceParseError

if __name__ == "__main__":
    try:
        raise SystemExit(run_extractor("python"))
    except SourceParseError as error:
        failure = {
            "code": error.code,
            "language": error.language,
            "path": error.path,
            "line": error.line,
            "column": error.column,
            "diagnostic": error.diagnostic,
        }
        print(f"modwire-error:{json.dumps(failure, ensure_ascii=False, separators=(',', ':'))}", file=sys.stderr)
        raise SystemExit(1) from error
