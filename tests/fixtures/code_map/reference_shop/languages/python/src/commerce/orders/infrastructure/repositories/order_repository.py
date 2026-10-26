from pathlib import Path

from commerce.orders.domain.model.order import Order


class OrderRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, order: Order) -> str:
        destination = self.root / order.order_id
        destination.write_text("placed", encoding="utf-8")
        return str(destination)
