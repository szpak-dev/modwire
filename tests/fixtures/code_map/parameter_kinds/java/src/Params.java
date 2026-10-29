class Params {
    String exampleParameters(String exampleValue, String... exampleRest) {
        return exampleValue + String.join("", exampleRest);
    }
}
