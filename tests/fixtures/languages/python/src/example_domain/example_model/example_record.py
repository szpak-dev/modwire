from uuid import UUID


class ExampleRecord:
    def __init__(self, example_id: str, example_active: bool = False) -> None:
        self.example_id = str(UUID(example_id))
        self.example_active = example_active
        self.example_name = None

    def example_action(self) -> None:
        self.example_active = True
