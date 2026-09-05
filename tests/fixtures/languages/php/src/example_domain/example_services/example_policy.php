<?php
namespace ExampleApp\ExampleDomain\ExampleServices;

use ExampleApp\ExampleDomain\ExampleModel\ExampleRecord;

final class ExamplePolicy
{
    public function example_allows(ExampleRecord $example_record): bool
    {
        return exampleAllowed($example_record);
    }
}

function exampleAllowed(ExampleRecord $example_record): bool
{
    return !$example_record->example_active;
}
