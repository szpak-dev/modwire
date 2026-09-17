from .configuration_value import ConfigurationValue


class BoundaryRule(ConfigurationValue):
    source: str
    realm: str = ""
    disallow: tuple[str, ...] = ()
    allow: tuple[str, ...] = ()
    allow_same_match: bool = False
