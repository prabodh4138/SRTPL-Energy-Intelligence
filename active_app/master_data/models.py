from dataclasses import dataclass
from typing import Optional

@dataclass
class Plaza:
    plaza_id: Optional[str]
    plaza_code: str
    plaza_name: str
    active: bool = True

@dataclass
class Asset:
    asset_id: Optional[str]
    asset_code: str
    asset_type: str
    plaza_id: Optional[str]
    location: Optional[str] = None
    active: bool = True

@dataclass
class Parameter:
    parameter_id: Optional[str]
    parameter_code: str
    parameter_name: str
    unit: Optional[str]
    data_type: str
    cumulative: bool = False
    active: bool = True

@dataclass
class AssetParameter:
    asset_parameter_id: Optional[str]
    asset_id: str
    parameter_id: str
    required: bool = False
    collection_frequency: Optional[str] = None
    active: bool = True

@dataclass
class Threshold:
    threshold_id: Optional[str]
    parameter_id: str
    condition_code: str
    warning_value: Optional[float]
    critical_value: Optional[float]
    unit: Optional[str]
    active: bool = True

@dataclass
class Tariff:
    tariff_id: Optional[str]
    tariff_code: str
    tariff_name: str
    energy_rate: Optional[float]
    demand_rate: Optional[float]
    fixed_charge: Optional[float]
    effective_from: str
    effective_to: Optional[str] = None
    active: bool = True

@dataclass
class KPIDefinition:
    kpi_id: Optional[str]
    kpi_code: str
    kpi_name: str
    formula_code: str
    unit: Optional[str]
    scope: str
    version: int
    active: bool = True
