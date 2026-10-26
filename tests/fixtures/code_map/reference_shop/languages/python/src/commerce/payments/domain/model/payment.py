class Payment:
    def __init__(self, payment_id: str) -> None:
        self.payment_id = payment_id
        self.captured = False

    def capture(self) -> None:
        self.captured = True
