from .declaration_identity import DeclarationIdentity
from .source_callable_symbol import SourceCallableSymbol


class SourceFunction(SourceCallableSymbol):
    declaration_id: DeclarationIdentity
