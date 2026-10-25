def energy_cost(kwh, tariff):
    return None if kwh is None or tariff is None else kwh*tariff
def cost_per_kwh(cost, kwh):
    return None if cost is None or kwh in (None,0) else cost/kwh
def solar_savings(solar_kwh, avoided_tariff):
    return None if solar_kwh is None or avoided_tariff is None else solar_kwh*avoided_tariff
