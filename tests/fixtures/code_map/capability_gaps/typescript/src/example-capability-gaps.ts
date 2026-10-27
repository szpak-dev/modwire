function ExampleClassDecorator<T extends new (...exampleArguments: never[]) => object>(
    exampleTarget: T,
): T {
    return exampleTarget;
}

function ExampleMethodDecorator(
    exampleTarget: object,
    exampleProperty: string,
    exampleDescriptor: PropertyDescriptor,
): void {
    void exampleTarget;
    void exampleProperty;
    void exampleDescriptor;
}

export namespace ExampleNamespace {
    export const exampleValue = 'example_namespace';
}

@ExampleClassDecorator
export class ExampleAssignedValue implements ExampleFirst {
    readonly exampleValue = 'example_value';

    @ExampleMethodDecorator
    exampleMethod(): string {
        return this.exampleValue;
    }
}

export interface ExampleFirst {}
export interface ExampleSecond {}
export type ExampleCombined = ExampleFirst & ExampleSecond;

const ExampleRuntimeBase = ExampleAssignedValue;
export class ExampleRuntime extends ExampleRuntimeBase {}

ExampleAssignedValue.prototype.exampleRuntimeMember = 'example_runtime_member';
