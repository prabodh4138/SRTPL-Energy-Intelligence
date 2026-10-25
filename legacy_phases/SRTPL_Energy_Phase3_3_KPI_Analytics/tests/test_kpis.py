from datetime import datetime, timezone
from analytics.models import Reading
from analytics.sources.solar import daily_generation
from analytics.sources.dg import generation, runtime_hours, kwh_per_hour
from analytics.sources.eb import consumption
from analytics.sources.ups import availability_percent
from analytics.energy_balance import EnergyBalance

def dt(d): return datetime(2026,9,d,tzinfo=timezone.utc)

def test_solar():
    r=[Reading("SOLAR","S1","TP01",dt(1),{"cumulative_kwh":100}),
       Reading("SOLAR","S1","TP01",dt(2),{"cumulative_kwh":118}),
       Reading("SOLAR","S1","TP01",dt(3),{"cumulative_kwh":140})]
    assert daily_generation(r)==(40.0,"OK")

def test_decrease():
    r=[Reading("SOLAR","S1","TP01",dt(1),{"cumulative_kwh":100}),
       Reading("SOLAR","S1","TP01",dt(2),{"cumulative_kwh":90})]
    assert daily_generation(r)==(None,"CUMULATIVE_DECREASE")

def test_dg_efficiency():
    r=[Reading("DG","D1","TP01",dt(1),{"cumulative_kwh":100,"running_hours":10}),
       Reading("DG","D1","TP01",dt(2),{"cumulative_kwh":160,"running_hours":12})]
    g,_=generation(r); h,_=runtime_hours(r)
    assert kwh_per_hour(g,h)==30

def test_eb():
    r=[Reading("EB","E1","TP01",dt(1),{"kwh":1000}),
       Reading("EB","E1","TP01",dt(2),{"kwh":1125})]
    assert consumption(r)==(125.0,"OK")

def test_ups():
    r=[Reading("UPS","U1","TP03",dt(1),{"status":"NORMAL"}),
       Reading("UPS","U1","TP03",dt(2),{"status":"OFF"})]
    assert availability_percent(r)==50

def test_balance():
    b=EnergyBalance(100,20,30)
    assert b.recorded_input==150
    assert b.solar_contribution_percent==20
