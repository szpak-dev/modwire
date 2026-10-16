from src.backend.sales.orders.application.totals import subtotal


def tax() -> int:
    return subtotal() * 23 // 100
