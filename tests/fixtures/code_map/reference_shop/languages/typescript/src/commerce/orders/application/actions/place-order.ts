import { Order } from '../../domain/model/order';
import { OrderPolicy } from '../../domain/services/order-policy';

export class PlaceOrder {
    constructor(private readonly policy: OrderPolicy) {}

    place(order: Order): boolean {
        if (!this.policy.allows(order)) {
            return false;
        }
        order.markPlaced();
        return true;
    }
}
