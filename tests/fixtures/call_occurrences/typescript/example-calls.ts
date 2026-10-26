function exampleTarget(): number {
    return 1;
}

function exampleCaller(): void {
    exampleTarget();
    exampleTarget();
}
