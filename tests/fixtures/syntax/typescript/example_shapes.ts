export const EXAMPLE_CONSTANT = 'example_constant';
export let example_variable = 'example_variable';

export interface ExampleContract {
    example_optional?: string;
    example_required(example_value: string): string;
}

export type ExampleCallback = (example_value: string, example_suffix?: string) => string;

export type ExampleCallableObject = {
    (example_value: string, example_suffix?: string): string;
};

export abstract class ExampleAbstract {
    abstract example_required(example_value: string): string;

    example_concrete(): string {
        return 'example_value';
    }
}

export class ExampleImplementation extends ExampleAbstract implements ExampleContract {
    example_optional?: string;

    example_required(example_value: string): string {
        return example_value;
    }
}

export const example_arrow = (example_value: string): string => example_value;
