export class ExampleValue {
    exampleDeclared = 'declared';
}

(ExampleValue.prototype as ExampleValue & { exampleRuntimeMember?: string }).exampleRuntimeMember = 'runtime';
