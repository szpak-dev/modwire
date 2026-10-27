<?php
use DateTimeImmutable;

function exampleTimestamp(): string
{
    return (new DateTimeImmutable())->format('c');
}
