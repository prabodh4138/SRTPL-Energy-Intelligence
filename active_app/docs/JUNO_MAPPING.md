# JUNO Source Mapping

The source mapping layer allows report columns to evolve without rewriting the entire application.

Example conceptual mapping:
JUNO column → internal parameter → normalized reading

Mapping can define:
- report type
- source column
- target parameter
- transform
- required flag
- version
- active period

Original JUNO headings remain untouched in the stored file.
Mapping is applied during parsing/normalization.
