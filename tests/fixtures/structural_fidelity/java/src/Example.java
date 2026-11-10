package example;

import java.util.List;
import java.util.Map;

interface ExampleContract {}
class ExampleBase {}

final class ExampleOwner<T extends Number> extends ExampleBase implements ExampleContract {
    private final String exampleValue = "";
    class ExampleNested {
        String exampleMethod(String exampleValue) { return exampleValue; }
    }
    String exampleMethod(String exampleValue) { return exampleValue; }
    int exampleMethod(int exampleValue) { return exampleValue; }
    void exampleParameters(String exampleValue, String... exampleRest) {}
    Map<String, List<? extends Number>> exampleTypes(Map<String, List<Integer>> exampleKnown,
                                                    Map<String, List<? extends Number>> exampleMixed,
                                                    String[] exampleArray) { return null; }
}

class ExampleOther {
    int exampleValue;
    int exampleMethod(int exampleValue) { return exampleValue; }
}

record ExampleRecord(String exampleName, int exampleCount) {}
enum ExampleStatus { EXAMPLE_READY, EXAMPLE_DONE }
