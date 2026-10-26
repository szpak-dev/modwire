class Order:
    def __init__(self, order_id: str) -> None:
        self.order_id = order_id
        self.placed = False

    def mark_placed(self) -> None:
        self.placed = True

    def is_placed(self) -> bool:
        return self.placed
