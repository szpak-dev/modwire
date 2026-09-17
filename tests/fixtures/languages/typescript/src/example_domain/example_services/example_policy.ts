import { ExampleRecord } from '../example_model/example_record';

export class ExamplePolicy {
    example_allows(example_record: ExampleRecord): boolean {
        return exampleAllowed(example_record);
    }
}

export function exampleAllowed(example_record) {
    return !example_record.example_active;
}
