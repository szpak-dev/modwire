import pytest

from .base_test import BoundaryTestCase


class TestPublicApiBoundaries(BoundaryTestCase):
    @pytest.mark.parametrize(
        ("target", "denied"),
        (
            ("src/modwire/application.py", False),
            ("src/modwire/autowiring.py", True),
            ("src/modwire/architecture/facade.py", True),
            ("src/modwire/architecture/map/application.py", True),
            ("src/modwire/architecture/map/services/example_service.py", True),
            ("src/modwire/shared/code/models/example_value.py", True),
            ("src/modwire/shared/code/services/example_service.py", True),
        ),
    )
    def test_only_the_public_application_is_importable_from_tests(self, target: str, denied: bool) -> None:
        config = self.application.load_configuration(self.repository / ".modwire")
        source = "tests/example_context/test_example.py"
        paths = self.violations(config, source, target)
        assert ((source, target) in paths) is denied

    def test_repository_rules_allow_inherited_test_helpers(self) -> None:
        config = self.application.load_configuration(self.repository / ".modwire")
        assert not self.violations(config, "tests/example_context/test_example.py", "tests/support/example_base.py")
