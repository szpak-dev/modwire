from modwire.architecture.config.models.configuration_value import ConfigurationValue


class FlowRealm(ConfigurationValue):
    name: str = ""
    module_tag: str = ""
    layers: tuple[str, ...] = ()
