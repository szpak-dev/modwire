from .source_symbol import SourceSymbol


class SourceCallableSymbol(SourceSymbol):
    declared_args: int
    optional_args: int
