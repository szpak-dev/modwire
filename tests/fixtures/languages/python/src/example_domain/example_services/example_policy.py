from example_domain.example_model.example_record import ExampleRecord


class ExamplePolicy:
    def example_allows(self, example_record: ExampleRecord) -> bool:
        return example_allowed(example_record)


def example_allowed(example_record: ExampleRecord) -> bool:
    return not example_record.example_active
