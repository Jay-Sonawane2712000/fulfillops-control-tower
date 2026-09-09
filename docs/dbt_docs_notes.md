# dbt Docs Notes

## Generate Docs

From the `transform/` directory, run:

```text
dbt docs generate --profiles-dir .
```

## Serve Docs Locally

From the `transform/` directory, run:

```text
dbt docs serve --profiles-dir .
```

dbt will print a local URL for browsing the generated project documentation.

## Generated Artifacts

dbt writes generated documentation artifacts to `transform/target/`. These files are build outputs and should not be committed.
