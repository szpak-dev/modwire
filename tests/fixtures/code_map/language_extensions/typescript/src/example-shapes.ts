import path from 'node:path';

export const EXAMPLE_CONSTANT = 'example_constant';
export let exampleVariable = 'example_variable';

export interface ExampleContract {
    exampleOptional?: string;
    exampleRequired(exampleValue: string): string;
}

export type ExampleCallback = (exampleValue: string, exampleSuffix?: string) => string;

export type ExampleCallableObject = {
    (exampleValue: string, exampleSuffix?: string): string;
};

export abstract class ExampleAbstract {
    abstract exampleRequired(exampleValue: string): string;

    exampleConcrete(): string {
        return 'example_value';
    }
}

export class ExampleImplementation extends ExampleAbstract implements ExampleContract {
    static exampleStatic = 'example_static';
    exampleOptional?: string;

    exampleRequired(exampleValue: string): string {
        return exampleValue;
    }

    examplePath(exampleRoot: string): string {
        return path.join(exampleRoot, this.exampleRequired('example'));
    }
}

export const exampleArrow = (exampleValue: string): string => exampleValue;
