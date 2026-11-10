<?php
namespace Example;

interface ExampleContract {}
interface ExampleLeft {}
interface ExampleRight {}
class ExampleBase {}
trait ExampleTrait {
    public function exampleTraitMethod(): string { return ''; }
}

final class ExampleOwner extends ExampleBase implements ExampleContract {
    use ExampleTrait;
    public function __construct(public readonly ?string $exampleValue = null) {}
    public function exampleMethod(string &$exampleReference, string $exampleDefault = '', string ...$exampleRest): string {
        return $exampleReference;
    }
    public function exampleTypes(ExampleLeft&ExampleRight $exampleIntersection, string|int $exampleUnion): ?string {
        return null;
    }
}

class ExampleOther {
    public int $exampleValue;
    public function exampleMethod(int $exampleValue): int { return $exampleValue; }
}

$exampleAnonymous = new class {
    public string $exampleValue;
    public function exampleMethod(string $exampleValue): string { return $exampleValue; }
};
