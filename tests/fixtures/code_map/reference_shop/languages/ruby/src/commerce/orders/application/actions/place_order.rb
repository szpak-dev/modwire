require_relative "../../domain/model/order"
require_relative "../../domain/services/order_policy"

class PlaceOrder
  def initialize(policy)
    @policy = policy
  end

  def place(order)
    return false unless @policy.allows(order)

    order.mark_placed
    true
  end
end
