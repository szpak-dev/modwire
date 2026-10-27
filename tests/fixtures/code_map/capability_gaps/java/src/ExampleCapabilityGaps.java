package example.capability.gaps;

import java.util.*;

@interface ExampleMarker {
    String exampleValue();
}

@ExampleMarker(exampleValue = "exampleRuntimeAnnotation")
sealed class ExampleBase permits ExampleChild {
    static final String exampleValue = "example_value";

    void exampleMethod() {}
}

final class ExampleChild extends ExampleBase {}
