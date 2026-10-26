from commerce.orders.domain.model.order import Order
from commerce.orders.domain.services.order_policy import OrderPolicy


class PlaceOrder:
    def __init__(self, policy: OrderPolicy) -> None:
        self.policy = policy

    def place(self, order: Order) -> bool:
        if not self.policy.allows(order):
            return False
        order.mark_placed()
        return True
