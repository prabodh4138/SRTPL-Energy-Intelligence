# Production Readiness Checklist

## Database
- [ ] Phase 2 schema applied
- [ ] Phase 4.5/4.6/4.7/4.8/4.9 SQL applied
- [ ] Required indexes present
- [ ] RLS reviewed
- [ ] RPC security reviewed
- [ ] Backups configured

## Storage
- [ ] `energy-original-files` bucket created
- [ ] Bucket private
- [ ] Storage policies reviewed
- [ ] Original CSV retrieval tested

## Application
- [ ] Authentication tested
- [ ] Environment variables configured
- [ ] Service-role key server-side only
- [ ] Navigation integrated
- [ ] Error handling enabled
- [ ] Logging enabled

## JUNO
- [ ] Solar sample tested
- [ ] DG sample tested
- [ ] EB sample tested
- [ ] Transformer sample tested
- [ ] UPS sample tested

## Analytics
- [ ] KPI formulas verified
- [ ] Tariffs verified
- [ ] Thresholds verified
- [ ] Transformer efficiency disabled pending confirmation
- [ ] EB MD unit confirmed before derived MD analytics

## Deployment
- [ ] Render build succeeds
- [ ] Health check succeeds
- [ ] Browser upload works
- [ ] Report download works
- [ ] Mobile browser checked
- [ ] Office laptop checked
