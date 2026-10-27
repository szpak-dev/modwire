final class Example {
    static String exampleTarget(String exampleValue) {
        return exampleValue;
    }

    static String exampleSource(String exampleValue) {
        exampleTarget(exampleValue);
        return exampleTarget(exampleValue);
    }
}
