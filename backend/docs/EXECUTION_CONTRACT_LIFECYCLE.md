# Execution Contract Lifecycle

## States

```
DRAFT → ACTIVE → DEPRECATED → ARCHIVED
```

| Status | Meaning | Executable by Future Runtime |
|---|---|---|
| `DRAFT` | Under development, not yet ready | No |
| `ACTIVE` | Canonical, valid, and immutable | Yes |
| `DEPRECATED` | Superseded by a newer version | No |
| `ARCHIVED` | Retired, kept for history only | No |

## Versioning

Contract IDs embed the version: `creative.promotional_video.v1`

When a contract requires changes:
1. Create a new contract with `version=2` and `status=DRAFT`
2. Validate and test the new contract
3. Set the new contract to `ACTIVE`
4. Set the old contract to `DEPRECATED`

**Never mutate an ACTIVE contract.** ACTIVE contracts are treated as immutable.

## Immutability Rule

An `ACTIVE` contract should not be silently changed. The `TeamExecutionContractValidator` will report a warning if a contract's `updated_at` post-dates its `created_at` while status is `ACTIVE`.

Future runtime systems may cache `ACTIVE` contracts. Silent mutation would create inconsistency.

## Resolution Behaviour

The `TeamExecutionContractResolver` only returns `ACTIVE` contracts.

If both `v1` (ACTIVE) and `v2` (DRAFT) exist for the same team+task_type, the resolver returns `v1` until `v2` is promoted to `ACTIVE`.
