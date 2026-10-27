@interface ExampleGenerated {
    String value();
}

@ExampleGenerated("exampleRuntimeMember")
final class Example {
    String exampleDeclared;
}
