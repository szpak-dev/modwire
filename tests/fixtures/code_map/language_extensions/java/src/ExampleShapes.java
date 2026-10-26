package example.shapes;

import java.time.Instant;

interface ExampleContract {
    String exampleRequired(String exampleValue);
}

abstract class ExampleAbstract {
    abstract String exampleRequired(String exampleValue);

    String exampleConcrete() {
        return "example_value";
    }
}

final class ExampleImplementation extends ExampleAbstract implements ExampleContract {
    static final String EXAMPLE_CONSTANT = "example_constant";
    String exampleOptional;

    @Override
    public String exampleRequired(String exampleValue) {
        return exampleValue;
    }

    public String exampleTimestamp(String exampleValue) {
        return Instant.now() + exampleRequired(exampleValue);
    }
}

record ExampleRecord(String exampleName) {}

enum ExampleStatus {
    EXAMPLE_READY
}

@interface ExampleAnnotation {
    String exampleValue();
}
