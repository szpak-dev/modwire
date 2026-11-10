export interface ExampleContract {
    (exampleValue: string, exampleOptional?: number): boolean;
    new (exampleValue: string): ExampleOwner<string>;
    [exampleKey: string]: unknown;
    exampleMethod(exampleValue: string): string;
}

export type ExampleAlias = { exampleValue: string };
export type ExampleOtherAlias = { exampleValue: number };

export class ExampleOwner<T extends string> {
    constructor(public readonly exampleValue: T) {}

    exampleMethod(exampleValue: string): string;
    exampleMethod(exampleValue: number): number;
    exampleMethod(exampleValue: string | number): string | number {
        return exampleValue;
    }

    get exampleProperty(): T { return this.exampleValue; }
    set exampleProperty(exampleValue: T) {}
}

export class ExampleOther {
    exampleValue: number = 1;
    exampleMethod(exampleValue: number): number { return exampleValue; }
}

export function exampleParameters(
    exampleRequired: string,
    exampleDefault: string = '',
    exampleOptional?: number,
    ...exampleRest: string[]
): void {}

export function exampleTypes(
    exampleMixed: Map<string, Array<number | null>>,
    exampleTuple: [string, number],
    exampleCallback: (exampleValue: string) => number,
    { exampleValue }: ExampleAlias,
): void {}
