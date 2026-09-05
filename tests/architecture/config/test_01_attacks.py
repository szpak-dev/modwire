import pytest
from pydantic import ValidationError

from modwire.architecture import ArchitectureConfig
from tests.architecture.base_test import ArchitectureTestCase


class TestConfigurationAttacks(ArchitectureTestCase):
    @pytest.mark.parametrize("shape", ({}, {"realms": []}))
    def test_rejects_configuration_without_a_shape_realm(self, shape: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            ArchitectureConfig.model_validate({"shape": shape})

    def test_rejects_unknown_rule_realms(self) -> None:
        with pytest.raises(ValidationError, match="Unknown boundary rule realms"):
            ArchitectureConfig.model_validate({
                "boundaries": {"rules": [{"source": "example-source", "realm": "example-missing"}]},
                "shape": {"realms": [{"name": "example-source", "match": "src"}]},
            })

    def test_rejects_unknown_configuration_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            ArchitectureConfig.model_validate({**self.example_configuration().to_dict(), "example_typo": True})
