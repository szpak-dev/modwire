import { ExampleRecord } from '../../example_domain/example_model/example_record';
import { ExamplePolicy, exampleAllowed } from '../../example_domain/example_services/example_policy';

export class ExampleAction {
    example_execute(example_record: ExampleRecord): string {
        return new ExamplePolicy().example_allows(example_record) ? 'example_complete' : 'example_blocked';
    }
}

export function exampleCommand(example_record) {
    return example_record;
}

export function exampleLabel(example_record) {
    return exampleAllowed(example_record) ? 'example_allowed' : 'example_blocked';
}

export function exampleNullable(example_value: string | undefined): string {
    return example_value ?? 'example_missing';
}

export function exampleOptional(example_value?: string): string {
    return example_value ?? 'example_missing';
}
