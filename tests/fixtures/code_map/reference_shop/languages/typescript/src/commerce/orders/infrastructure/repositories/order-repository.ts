import path from 'node:path';

import { Order } from '../../domain/model/order';

export class OrderRepository {
    constructor(private readonly root: string) {}

    save(order: Order): string {
        return path.join(this.root, order.orderId);
    }
}
