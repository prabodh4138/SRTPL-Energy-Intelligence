# Role Based Access Control

## SUPER_ADMIN
Full application administration.

## ADMIN
Users/roles, master data, imports, reprocessing, configuration, reports and audit visibility.

## ENERGY_MANAGER
Energy imports, reprocessing, analytics, reports and audit visibility.

## PLAZA_MANAGER
Operational access for permitted plaza scope.

## OPERATOR
JUNO import and operational/report access according to assigned scope.

## AUDITOR
Read-only audit, validation, exception and report access.

## VIEWER
Read-only dashboard/report access.

### Scope
Permissions must support:
- global
- plaza
- asset/equipment where required

Never rely only on hidden Streamlit menu items for security. Authorization must also exist server-side/RLS/RPC level.
