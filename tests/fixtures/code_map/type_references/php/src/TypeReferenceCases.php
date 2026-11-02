<?php

class ExampleType {}
class ExampleResult {}

function exampleTypes(ExampleType $exampleNested, string|int $exampleUnsupported, $exampleAbsent): ExampleResult
{
    return new ExampleResult();
}
