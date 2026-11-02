from dataclasses import dataclass

from modwire.application import DeclarationIdentity


@dataclass(frozen=True)
class DeclarationIdentityKey:
    identity: DeclarationIdentity
