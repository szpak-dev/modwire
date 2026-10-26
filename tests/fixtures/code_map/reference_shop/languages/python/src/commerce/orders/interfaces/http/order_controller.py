from commerce.orders.application.actions.place_order import PlaceOrder
from commerce.orders.domain.model.order import Order


class OrderController:
    def __init__(self, action: PlaceOrder) -> None:
        self.action = action

    def handle(self, order_id: str) -> bool:
        return self.action.place(Order(order_id))
