# Output Contract Model

## Identity
Each `OutputContract` serves as an aggregate root with a unique `output_contract_id` and `version`.

## Output Types
A logical output type system includes:
- `TEXT`, `STRUCTURED_DATA`, `DOCUMENT`, `REPORT`, `CODE`, `CODE_PACKAGE`, `IMAGE`, `AUDIO`, `VIDEO`, `PRESENTATION`, `DATASET`, `ARCHIVE`, `ARTIFACT`, `PACKAGE`.

## Cardinality
`ONE`, `MANY`, `OPTIONAL`.

## Formats
A list of allowed formats (e.g. `["mp4", "webm"]`).

## Artifact Policy
Dictates if a physical file is expected:
- `REQUIRED`
- `OPTIONAL`
- `NONE`

## Delivery Policy
- `USER_DOWNLOAD`: Expects to be served to the frontend.
- `INLINE`: Consumed natively within a text view.
- `REFERENCE`: Passed strictly internally.
- `MULTI_ARTIFACT`: Part of a package.

## Constraints
`metadata_requirements` specify hard key-value matches (e.g. `{"resolution": "1080p"}`). 
`content_requirements` declare semantic requirements for Quality Gates to evaluate (e.g. `["must contain summary"]`).
