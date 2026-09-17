<?php
namespace ExampleApp\ExampleApplication\ExampleActions;

use ExampleApp\ExampleDomain\ExampleModel\ExampleRecord;
use ExampleApp\ExampleDomain\ExampleServices\ExamplePolicy;

final class ExampleAction
{
    public function example_execute(ExampleRecord $example_record): string
    {
        return (new ExamplePolicy())->example_allows($example_record) ? 'example_complete' : 'example_blocked';
    }
}

function exampleCommand(ExampleRecord $example_record): ExampleRecord
{
    return $example_record;
}

function exampleLabel(ExampleRecord $example_record): string
{
    return $example_record->example_active ? 'example_blocked' : 'example_allowed';
}

function exampleNullable(?string $example_value): string
{
    return $example_value ?? 'example_missing';
}
