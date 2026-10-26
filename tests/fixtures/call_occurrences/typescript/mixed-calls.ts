class ExampleValue {}

function exampleInner(): number {
    return 1;
}

function exampleOuter(exampleValue: number): number {
    return exampleValue;
}

function exampleMixedCaller(): void {
    exampleOuter(exampleInner());
    new ExampleValue();
}
