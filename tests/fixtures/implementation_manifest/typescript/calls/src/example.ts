export function exampleTarget(exampleValue: string): string {
    return exampleValue;
}

export function exampleSource(exampleValue: string): string {
    exampleTarget(exampleValue);
    return exampleTarget(exampleValue);
}
