-- Seed only structural reference data here; do not seed fake operational assets.
-- Actual TP01/TP02/TP03 assets, meter IDs and equipment relationships
-- should be loaded from approved project master data.

insert into energy_master.config_version
(domain, entity_id, version_no, effective_from, active)
values
('SYSTEM', 'SRTPL-ENERGY', 1, current_date, true)
on conflict (domain, entity_id, version_no) do nothing;
