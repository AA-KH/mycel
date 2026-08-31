# Python Environment Audit

## Current Environment State

Based on the repository audit, the environment configurations are currently mapped as follows:

1. **Docker Container Environment (Production / Staging)**
   - **Base Image**: `python:3.11-slim` (Defined in `backend/Dockerfile`)
   - **Dependencies**: Installed system-wide in the container via `pip install --no-cache-dir -r requirements.txt`.
   
2. **Local Development Environment**
   - The repository root contains a `venv/` directory, indicating local virtual environment usage.
   - The user's host machine might be running Python 3.12 or newer (as evidenced by syntax parser differences during local execution probes).

## Package Compatibility

The current `requirements.txt` specifies heavily constrained versions:
```text
fastapi~=0.129.0
uvicorn[standard]~=0.41.0
python-multipart~=0.0.22
aio-pika~=9.6.0
motor~=3.7.0
pydantic[email]~=2.12.5
python-dotenv~=1.2.1
loguru~=0.7.3
PyJWT[crypto]~=2.11.0
passlib[bcrypt]~=1.7.4
bcrypt==3.2.2
groq
armoriq-sdk
```

## Recommendations

**Target Python Version**: `Python 3.11`

**Reasoning**:
1. **Consistency**: The `Dockerfile` explicitly relies on Python 3.11. To prevent "works on my machine" bugs, the local `venv/` should ideally mirror the production container.
2. **Compatibility**: Packages like `motor`, `aio-pika`, and `bcrypt` involve C-extensions and asyncio bindings that are highly stable in 3.11. Moving prematurely to 3.12 or 3.13 without comprehensive testing of the `armoriq-sdk` or `groq` async implementations may introduce underlying event loop issues or compilation failures.
3. **Typing**: Python 3.11 provides excellent native typing features (`Self`, `NotRequired`, `LiteralString`) which will be critical when designing the strict `Employee` and `Artifact` models, without the churn of the newest 3.12 syntax changes.

## Actionable Constraints

- Do **not** modify `requirements.txt` or upgrade the `Dockerfile` base image without explicit approval.
- Ensure any local development tools or CI/CD pipelines enforce a `Python 3.11` runtime check to match the container.
