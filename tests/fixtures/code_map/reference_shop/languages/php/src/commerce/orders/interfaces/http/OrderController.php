<?php
namespace ModwireFixture\Commerce\Orders\Interfaces\Http;

use ModwireFixture\Commerce\Orders\Application\Actions\PlaceOrder;
use ModwireFixture\Commerce\Orders\Domain\Model\Order;

final class OrderController
{
    public function __construct(private readonly PlaceOrder $action) {}

    public function handle(string $orderId): bool
    {
        return $this->action->place(new Order($orderId));
    }
}
