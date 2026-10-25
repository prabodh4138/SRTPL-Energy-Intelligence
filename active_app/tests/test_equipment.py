from equipment.fields import EQUIPMENT_FIELDS
from equipment.services import EquipmentDashboardService

def test_all_equipment_types_exist():
    service = EquipmentDashboardService()
    assert set(service.available_types()) == {"SOLAR","DG","EB","TRANSFORMER","UPS"}

def test_field_catalogs_exist():
    for equipment in ["SOLAR","DG","EB","TRANSFORMER","UPS"]:
        assert EQUIPMENT_FIELDS[equipment]

def test_unknown_assets_are_empty_until_master_data():
    service = EquipmentDashboardService()
    assert service.available_assets("DG") == []
