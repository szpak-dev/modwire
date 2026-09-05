<?php
namespace ExampleApp\ExampleInterfaces\ExampleHttp;

use ExampleApp\ExampleApplication\ExampleActions\ExampleAction;
use ExampleApp\ExampleApplication\ExampleActions\exampleCommand;
use ExampleApp\ExampleDomain\ExampleModel\ExampleRecord as ExampleRecordAlias;
use DateTimeImmutable as ExampleTimestamp;

final class ExampleController
{
    public function __construct(private ExampleAction $exampleAction) {}

    public function example_handle(ExampleRecordAlias $example_record): string
    {
        $example_timestamp = new ExampleTimestamp();
        return $this->exampleAction->example_execute(exampleCommand($example_record)) . $example_timestamp->format('c');
    }
}
