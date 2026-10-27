<?php
class ExampleValue
{
    public string $exampleDeclared = 'declared';
}

$exampleValue = new ExampleValue();
$exampleValue->exampleRuntimeMember = 'runtime';
