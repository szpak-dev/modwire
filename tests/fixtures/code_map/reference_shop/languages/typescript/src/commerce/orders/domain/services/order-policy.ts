import { Order } from '../model/order';

export class OrderPolicy {
    allows(order: Order): boolean {
        return !order.isPlaced();
    }
}
