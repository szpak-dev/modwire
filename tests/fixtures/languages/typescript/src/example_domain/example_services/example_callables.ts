export const example_a = 1, example_b = 2;

export const example_typed: (example_value: string) => string = (example_value: string) => example_value.trim();

export const example_generic = <T>(example_value: T): T => example_value;

export const example_destructured = ({ example_id }: { example_id: string }) => example_id.toUpperCase();

export default () => example_typed('default');

export const example_handlers = {
    example_inline: () => example_typed('example_inline'),
    example_method(example_value: string) {
        return example_generic(example_value);
    },
    example_nested: {
        example_run: function (example_value: string) {
            return example_destructured({ example_id: example_value });
        },
    },
};

export class ExampleCallables {
    example_handler = (example_value: string) => example_typed(example_value);
}
