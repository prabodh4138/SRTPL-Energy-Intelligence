from energy_validation.cumulative import cumulative_delta

def test_normal_delta():
    assert cumulative_delta(120, 100) == (20.0, "NORMAL")

def test_reset_not_negative_consumption():
    delta, state = cumulative_delta(20, 100)
    assert delta == -80.0
    assert state == "DECREASE"

def test_missing():
    assert cumulative_delta(None, 100)[1] == "INSUFFICIENT_DATA"
