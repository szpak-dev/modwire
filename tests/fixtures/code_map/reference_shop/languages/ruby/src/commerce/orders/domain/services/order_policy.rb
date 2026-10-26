require_relative "../model/order"

class OrderPolicy
  def allows(order)
    !order.is_placed
  end
end
