# Spec migrations

`spec_version` `1.0` is the baseline. There is nothing to migrate yet.

Rules for every later version:

- Migrate a spec when it is read. Keep the stored row unchanged until the user saves again.
- A save writes a new version row. Set `parent_version` to the row it came from.
- Deprecate a block type when it should stop being used. Leave the old type in the migration path so saved strategies still open.
- Do not delete a block type that any saved spec might still name.
