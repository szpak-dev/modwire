package example.shapes;

interface ExampleContract {
    String example_required(String example_value);
}

abstract class ExampleAbstract {
    abstract String example_required(String example_value);

    String example_concrete() {
        return "example_value";
    }
}

final class ExampleImplementation extends ExampleAbstract implements ExampleContract {
    String example_optional;

    @Override
    public String example_required(String example_value) {
        return example_value;
    }
}

record ExampleRecord(String example_name) {}

enum ExampleStatus {
    EXAMPLE_READY
}

@interface ExampleAnnotation {
    String example_value();
}
