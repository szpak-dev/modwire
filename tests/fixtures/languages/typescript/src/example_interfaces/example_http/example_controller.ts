import * as path from 'node:path';

import { ExampleAction, exampleCommand } from '../../example_application/example_actions/example_action';
import type { ExampleRecord as ExampleRecordAlias } from '../../example_domain/example_model/example_record';

export class ExampleController {
    constructor(private readonly exampleAction: ExampleAction) {}

    example_handle(example_record: ExampleRecordAlias): string {
        const example_command = exampleCommand(example_record);
        return path.join(this.exampleAction.example_execute(example_command), example_record.example_id);
    }
}
