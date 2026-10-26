from commerce.orders.domain.model.order import Order


class OrderPolicy:
    def allows(self, order: Order) -> bool:
        return not order.is_placed()
