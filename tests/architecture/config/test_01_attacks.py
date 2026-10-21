import pytest
from pydantic import ValidationError

from modwire.application import ArchitectureConfigValidationError, ArchitectureConfigViolation

from ..base_test import ArchitectureTestCase


class TestConfigurationAttacks(ArchitectureTestCase):
    @pytest.mark.parametrize(
        "boundaries",
        (
            {"tags": [{"name": "example-tag", "match": "src"}, {"name": "example-tag", "match": "tests"}]},
            {"flow": {"realms": [{"name": "example-realm"}, {"name": "example-realm"}]}},
            {"flow": {"analyzers": ["no-cycles", "no-cycles"]}},
            {"tags": [{"name": "", "match": "src"}]},
            {"tags": [{"name": "example-tag", "match": ""}]},
            {"example_typo": True},
        ),
    )
    def test_rejects_ambiguous_or_malformed_boundary_configuration(self, boundaries: dict[str, object]) -> None:
        with pytest.raises(ArchitectureConfigValidationError):
            self.application.configure({**self.example_configuration().to_dict(), "boundaries": boundaries})

    @pytest.mark.parametrize("limit", (-2, "example_invalid", None))
    def test_rejects_invalid_shape_thresholds(self, limit: object) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure(
                {
                    "shape": {
                        "realms": [{"name": "example-source", "match": "*", "shape": {"max_classes_per_file": limit}}]
                    }
                }
            )
        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert raised.value.subject == "architecture configuration"
        assert isinstance(raised.value.__cause__, ValidationError)

    def test_rejects_unknown_import_crossing_type(self) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure(
                {
                    "shape": {
                        "realms": [
                            {
                                "name": "example-source",
                                "match": "*",
                                "shape": {"allowed_import_crossing_types": ["module", "example_invalid"]},
                            }
                        ]
                    }
                }
            )
        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert isinstance(raised.value.__cause__, ValidationError)

    @pytest.mark.parametrize("shape", ({}, {"realms": []}))
    def test_rejects_configuration_without_a_shape_realm(self, shape: dict[str, object]) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure({"shape": shape})
        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert isinstance(raised.value.__cause__, ValidationError)

    def test_rejects_unknown_rule_realms(self) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure(
                {
                    "boundaries": {"rules": [{"source": "example-source", "realm": "example-missing"}]},
                    "shape": {"realms": [{"name": "example-source", "match": "src"}]},
                }
            )
        assert raised.value.violation is ArchitectureConfigViolation.UNKNOWN_BOUNDARY_REALM
        assert raised.value.subject == "example-missing"

    def test_rejects_unknown_configuration_fields(self) -> None:
        with pytest.raises(ArchitectureConfigValidationError) as raised:
            self.application.configure({**self.example_configuration().to_dict(), "example_typo": True})
        assert raised.value.violation is ArchitectureConfigViolation.INVALID_CONFIGURATION
        assert isinstance(raised.value.__cause__, ValidationError)
