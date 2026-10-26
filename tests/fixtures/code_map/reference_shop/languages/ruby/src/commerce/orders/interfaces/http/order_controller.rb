require_relative "../../application/actions/place_order"
require_relative "../../domain/model/order"

class OrderController
  def initialize(action)
    @action = action
  end

  def handle(order_id)
    @action.place(Order.new(order_id))
  end
end
