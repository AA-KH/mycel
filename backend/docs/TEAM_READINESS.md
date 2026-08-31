# Team Readiness

The `TeamReadiness` enum categorizes the validation state of any individual Mycel team.

## READY
The Team configuration is completely valid and functionally operational. 
- Identity parameters exist.
- Required workforce counts are met.
- Inter-system references match.
- Capability Resolution succeeds.

## READY_WITH_WARNINGS
The Team lacks a non-critical metadata field (e.g. description) or possesses configuration that may impact display, but will not functionally halt Task Routing or Pipeline Execution.
- Under `strict=True` validation runs, `READY_WITH_WARNINGS` is elevated and demoted to `NOT_READY`.

## NOT_READY
The Team has failed one or more critical capability, registry, isolation, identity, or pipeline tests. 
- Resolvers will not utilize this team.
- At least one `ValidationIssue` exists with `severity="ERROR"`.
