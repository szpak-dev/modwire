<?php
namespace ModwireFixture\Commerce\Payments\Application\Actions;

use ModwireFixture\Commerce\Payments\Domain\Model\Payment;

final class CapturePayment
{
    public function capture(Payment $payment): void
    {
        $payment->capture();
    }
}
