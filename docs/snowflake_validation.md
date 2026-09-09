# Snowflake Validation Setup

Snowflake validation is prepared for FulfillOps Control Tower, but it has not been executed in this repository. DuckDB remains the local development warehouse. Snowflake is a separate validation target for proving the dbt models can run in a cloud warehouse once credentials and objects are configured.

## Required Setup Fields

Configure these values outside git, either as environment variables or in a local dbt profile copied from `transform/profiles_snowflake.yml.example`:

- `SNOWFLAKE_ACCOUNT`
- `SNOWFLAKE_USER`
- `SNOWFLAKE_PASSWORD` or `SNOWFLAKE_AUTHENTICATOR`
- `SNOWFLAKE_ROLE`
- `SNOWFLAKE_WAREHOUSE`
- `SNOWFLAKE_DATABASE`
- `SNOWFLAKE_SCHEMA`

Do not commit real credentials.

## Snowflake Trial Validation Steps

1. Create a Snowflake trial account.
2. Create a warehouse, database, and schema for validation.
3. Load or recreate the required bronze source tables in Snowflake.
4. Copy `transform/profiles_snowflake.yml.example` to a local untracked profile location.
5. Fill in the placeholder values using environment variables or local-only credentials.
6. From `transform/`, run:

```text
dbt debug --profiles-dir . --profile fulfillops_transform_snowflake
```

7. If debug passes, run:

```text
dbt build --profiles-dir . --profile fulfillops_transform_snowflake
```

## Notes

The default project profile remains DuckDB for local development at `../warehouse/fulfillops.duckdb`. Snowflake validation should be treated as a deployment-readiness check, not as the primary local workflow.
