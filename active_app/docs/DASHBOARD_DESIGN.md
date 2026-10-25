# Executive Dashboard Design

## Top KPI row
1. EB Consumption
2. DG Generation
3. Solar Generation
4. Energy Cost
5. Solar Saving

## Second row
- Energy mix
- Data quality

## Third row
- TP01 / TP02 / TP03 comparison

## Fourth row
- EB / DG / Solar trend

## Fifth row
- Exceptions requiring attention

## Drill-down
Management KPI
→ Plaza
→ Asset
→ Parameter
→ KPI Result
→ Normalized Reading
→ Raw JUNO Record
→ Import Row
→ Original JUNO CSV

## UX rules
- Filters always visible.
- Empty data must show a clear message, never fake zeroes.
- NULL is not displayed as 0.
- No KPI calculation should be implemented in the UI layer.
- Mobile layout must remain usable.
