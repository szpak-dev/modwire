final class ExampleMixedCalls {
    static final class ExampleValue {}

    static int exampleInner() {
        return 1;
    }

    static int exampleOuter(int exampleValue) {
        return exampleValue;
    }

    static void exampleMixedCaller() {
        exampleOuter(exampleInner());
        new ExampleValue();
    }
}
