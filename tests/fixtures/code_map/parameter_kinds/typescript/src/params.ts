export function exampleParameters(exampleValue: string, ...exampleRest: string[]): string {
    return exampleValue + exampleRest.join('');
}
