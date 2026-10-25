"""
Maps parsed JUNO records to the raw schema.

The parser may evolve independently from this mapper.
The source_payload field always receives the complete parsed source row.
"""

def _v(values, *names):
    for name in names:
        if name in values:
            return values[name]
    return None

def map_solar(record):
    v = record.values
    return {
        "import_row_id": record.import_row_id,
        "solar_plant_id": _v(v, "solarplantid", "solar_plant_id"),
        "reading_datetime": _v(v, "date"),
        "cumulative_kwh": _v(v, "unit_generated_in_kwh"),
        "remarks": _v(v, "remarks"),
        "created_by": _v(v, "created_by"),
        "source_created_on": _v(v, "created_on"),
        "source_payload": record.raw_payload,
    }

def map_dg(record):
    v = record.values
    return {
        "import_row_id": record.import_row_id,
        "dg_id": _v(v, "dg_id"),
        "reading_datetime": _v(v, "date", "date_time"),
        "status": _v(v, "status"),
        "kva": _v(v, "kva"),
        "kw": _v(v, "kw"),
        "voltage_ry": _v(v, "voltage_ry"),
        "voltage_yb": _v(v, "voltage_yb"),
        "voltage_br": _v(v, "voltage_br"),
        "current_r": _v(v, "current_r"),
        "current_y": _v(v, "current_y"),
        "current_b": _v(v, "current_b"),
        "pf": _v(v, "pf"),
        "diesel_level": _v(v, "diesel_level"),
        "diesel_topup": _v(v, "diesel_top_up", "diesel_topup"),
        "load_percent": _v(v, "load_percent"),
        "cumulative_kwh": _v(v, "kwh"),
        "cumulative_running_hours": _v(v, "running_hours"),
        "rpm": _v(v, "rpm"),
        "remarks": _v(v, "remarks"),
        "created_by": _v(v, "created_by"),
        "source_created_on": _v(v, "created_on"),
        "source_payload": record.raw_payload,
    }

def map_eb(record):
    v = record.values
    return {
        "import_row_id": record.import_row_id,
        "meter_id": _v(v, "eb_meter_id", "meter_id"),
        "consumer_number": _v(v, "consumer_number"),
        "location": _v(v, "location"),
        "category": _v(v, "category"),
        "reading_datetime": _v(v, "date"),
        "kwh": _v(v, "kwh"),
        "kvah": _v(v, "kvah"),
        "kvarh": _v(v, "kvarh"),
        "md": _v(v, "md"),
        "pf": _v(v, "pf"),
        "remarks": _v(v, "remarks"),
        "created_by": _v(v, "created_by"),
        "source_created_on": _v(v, "created_on"),
        "source_payload": record.raw_payload,
    }

def map_transformer(record):
    v = record.values
    return {
        "import_row_id": record.import_row_id,
        "transformer_id": _v(v, "transformer_id"),
        "location": _v(v, "location"),
        "reading_datetime": _v(v, "date"),
        "primary_v_ry": _v(v, "primary_side_voltage_ry"),
        "primary_v_yb": _v(v, "primary_side_voltage_yb"),
        "primary_v_br": _v(v, "primary_side_voltage_br"),
        "primary_i_r": _v(v, "primary_side_amps_r"),
        "primary_i_y": _v(v, "primary_side_amps_y"),
        "primary_i_b": _v(v, "primary_side_amps_b"),
        "secondary_v_ry": _v(v, "secondary_side_voltage_ry"),
        "secondary_v_yb": _v(v, "secondary_side_voltage_yb"),
        "secondary_v_br": _v(v, "secondary_side_voltage_br"),
        "secondary_i_r": _v(v, "secondary_side_amps_r"),
        "secondary_i_y": _v(v, "secondary_side_amps_y"),
        "secondary_i_b": _v(v, "secondary_side_amps_b"),
        "kwh": _v(v, "kwh"),
        "kvah": _v(v, "kvah"),
        "pf": _v(v, "pf"),
        "frequency": _v(v, "freq", "frequency"),
        "wti": _v(v, "temperature_wti", "wti"),
        "oti": _v(v, "temperature_oti", "oti"),
        "created_by": _v(v, "created_by"),
        "source_created_on": _v(v, "created_on"),
        "source_payload": record.raw_payload,
    }

def map_ups(record):
    v = record.values
    return {
        "import_row_id": record.import_row_id,
        "ups_id": _v(v, "ups_id"),
        "location": _v(v, "location"),
        "reading_datetime": _v(v, "date"),
        "main_input_v_r": _v(v, "main_input_voltage_r"),
        "main_input_v_y": _v(v, "main_input_voltage_y"),
        "main_input_v_b": _v(v, "main_input_voltage_b"),
        "main_input_i_r": _v(v, "main_input_current_r"),
        "main_input_i_y": _v(v, "main_input_current_y"),
        "main_input_i_b": _v(v, "main_input_current_b"),
        "rectifier_voltage": _v(v, "main_input_rectifier_voltage"),
        "bypass_voltage": _v(v, "by_pass_voltage", "bypass_voltage"),
        "bypass_current": _v(v, "by_pass_current", "bypass_current"),
        "bypass_frequency": _v(v, "by_pass_fr_48_to_52_hz", "bypass_frequency"),
        "output_voltage": _v(v, "output_voltage"),
        "output_current": _v(v, "output_current"),
        "output_frequency": _v(v, "output_fr_48_to_52_hz", "output_frequency"),
        "battery_temperature": _v(v, "battery_tem"),
        "battery_vdc": _v(v, "battery_vdc"),
        "battery_ib": _v(v, "battery_ib"),
        "created_by": _v(v, "created_by"),
        "source_created_on": _v(v, "created_on"),
        "source_payload": record.raw_payload,
    }

RAW_MAPPERS = {
    "SOLAR": ("juno_solar", map_solar),
    "DG": ("juno_dg", map_dg),
    "EB": ("juno_eb", map_eb),
    "TRANSFORMER": ("juno_transformer", map_transformer),
    "UPS": ("juno_ups", map_ups),
}
