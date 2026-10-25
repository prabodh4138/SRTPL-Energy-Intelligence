# Security Baseline

- Supabase service credentials must remain server-side.
- Never expose service-role keys to browser/client code.
- Use RLS for production tables.
- Use private Storage for original JUNO CSV files.
- Do not store plaintext user passwords.
- Keep ADMIN_TOKEN in deployment secrets, never in Git.
- Every import and manual correction must have an audit trail.
- Roles should be enforced server-side/database-side, not only by hiding Streamlit menu items.
