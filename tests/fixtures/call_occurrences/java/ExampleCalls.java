final class ExampleCalls {
    static int exampleTarget() {
        return 1;
    }

    static void exampleCaller() {
        exampleTarget();
        exampleTarget();
    }
}
