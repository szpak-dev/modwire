<?php
namespace ModwireFixture\Commerce\Orders\Application\Actions;

use ModwireFixture\Commerce\Orders\Domain\Model\Order;
use ModwireFixture\Commerce\Orders\Domain\Services\OrderPolicy;

final class PlaceOrder
{
    public function __construct(private readonly OrderPolicy $policy) {}

    public function place(Order $order): bool
    {
        if (!$this->policy->allows($order)) {
            return false;
        }
        $order->markPlaced();
        return true;
    }
}
