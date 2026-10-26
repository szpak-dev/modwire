<?php
namespace ModwireFixture\Commerce\Payments\Domain\Model;

final class Payment
{
    private bool $captured = false;

    public function __construct(public readonly string $paymentId) {}

    public function capture(): void
    {
        $this->captured = true;
    }
}
