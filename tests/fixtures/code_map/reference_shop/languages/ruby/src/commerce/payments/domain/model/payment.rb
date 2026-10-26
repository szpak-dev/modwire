class Payment
  def initialize(payment_id)
    @payment_id = payment_id
    @captured = false
  end

  def capture
    @captured = true
  end
end
