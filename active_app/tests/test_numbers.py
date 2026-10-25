from energy_validation.numbers import percent_imbalance

def test_imbalance():
    assert round(percent_imbalance([100, 100, 110]), 2) == 6.45
