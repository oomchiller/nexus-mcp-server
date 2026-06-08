## Summary

Describe the change.

## Scope

- [ ] Nexus-specific
- [ ] No generic infrastructure/platform abstraction added
- [ ] Documentation updated if behavior changed
- [ ] Safety boundaries preserved

## Validation

```bash
uv run pytest
uv run ruff check .
uv run mypy src tests
```

## Nexus Compatibility

State tested or inferred Nexus versions.

## Safety Impact

Describe any effect on:

- `readonly`, `audit`, or `admin` mode;
- raw API behavior;
- write tools;
- host allowlist behavior;
- secret redaction.
