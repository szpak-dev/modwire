import crypto from 'node:crypto';

export class ExampleRecord {
    example_name?: string;

    constructor(public readonly example_id: string, public readonly example_active: boolean = false) {}

    example_fingerprint(): string {
        return crypto.createHash('sha1').update(this.example_id).digest('hex');
    }
}
