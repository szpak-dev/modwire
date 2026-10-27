package example.manifest;

import java.time.Instant;

interface ExampleContract {
    String exampleRequired(String exampleValue);
}

abstract class ExampleAbstract {
    abstract String exampleRequired(String exampleValue);
}

final class ExampleImplementation extends ExampleAbstract implements ExampleContract {
    static final String EXAMPLE_CONSTANT = "example";
    private final String exampleName;

    ExampleImplementation(String exampleName) {
        this.exampleName = exampleName;
    }

    @Override
    public String exampleRequired(String exampleValue) {
        return exampleValue;
    }

    public String exampleTimestamp(String exampleValue) {
        return Instant.now() + exampleRequired(exampleValue) + exampleName;
    }
}

record ExampleRecord(String exampleName) {}

enum ExampleStatus {
    EXAMPLE_READY
}

@interface ExampleAnnotation {
    String exampleValue();
}
