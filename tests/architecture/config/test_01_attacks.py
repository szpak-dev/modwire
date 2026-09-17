import pytest
from pydantic import ValidationError

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
        with pytest.raises(ValidationError):
            self.application.configure({**self.example_configuration().to_dict(), "boundaries": boundaries})

    @pytest.mark.parametrize("limit", (-2, "example_invalid", None))
    def test_rejects_invalid_shape_thresholds(self, limit: object) -> None:
        with pytest.raises(ValidationError):
            self.application.configure(
                {
                    "shape": {
                        "realms": [{"name": "example-source", "match": "*", "shape": {"max_classes_per_file": limit}}]
                    }
                }
            )

    @pytest.mark.parametrize("shape", ({}, {"realms": []}))
    def test_rejects_configuration_without_a_shape_realm(self, shape: dict[str, object]) -> None:
        with pytest.raises(ValidationError):
            self.application.configure({"shape": shape})

    def test_rejects_unknown_rule_realms(self) -> None:
        with pytest.raises(ValidationError, match="Unknown boundary rule realms"):
            self.application.configure(
                {
                    "boundaries": {"rules": [{"source": "example-source", "realm": "example-missing"}]},
                    "shape": {"realms": [{"name": "example-source", "match": "src"}]},
                }
            )

    def test_rejects_unknown_configuration_fields(self) -> None:
        with pytest.raises(ValidationError, match="extra_forbidden"):
            self.application.configure({**self.example_configuration().to_dict(), "example_typo": True})
