def CalcRefund(amount_wh, energy_cost_per_wh, capacity_wh):
    Refund = (capacity_wh - amount_wh) * energy_cost_per_wh
    return Refund



