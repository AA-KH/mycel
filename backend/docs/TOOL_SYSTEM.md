# Tool System Architecture

The Tool System in Mycel enforces a strict boundary between the LLM's **intent** and the platform's **execution**. It ensures that AI Employees can safely interact with external systems without exposing the underlying infrastructure to malicious prompts or unauthorized actions.

## Core Concepts

1. **Tool Definition**
   Every tool is defined by a canonical schema (`ToolDefinition`) which includes its `id`, `input_schema`, `output_schema`, `capabilities`, `risk_level`, and `timeout_seconds`. This schema is completely separated from the actual Python implementation.

2. **Tool Registry**
   A centralized `ToolRegistry` holds the definitions and implementations for all tools. It acts as the source of truth for tool resolution.

3. **Tool Security Policy**
   Before execution, every `ToolRequest` passes through the `ToolSecurityPolicy`. This layer:
   - Validates that the tool is enabled.
   - Validates that the specific Employee has permission to use the tool.
   - Enforces SSRF protection for network tools.
   - Enforces path traversal protection for filesystem tools.
   - Checks if human approval is required.

4. **Tool Executor**
   The `ToolExecutor` wraps the execution of the tool, enforcing the `timeout_seconds`, executing bounded retries for transient failures, and catching exceptions to normalize them into a standard `ToolResult`.

5. **Tool Gateway**
   The `CoreToolGateway` implements the `ToolGateway` interface from Phase 4. It acts as the glue layer, taking a `ToolRequest` from the `AgentRuntime`, validating it via the Security Policy, and executing it via the Executor.

## Security Mechanisms

### SSRF Protection
Web-based tools (like `browser.open` and `web.scrape`) pass their target URLs through `ToolSecurityPolicy.validate_ssrf()`. This blocks access to `localhost`, loopback addresses, AWS/GCP metadata endpoints, and internal network ranges.

### Filesystem Sandbox
Filesystem tools (`filesystem.read`, `filesystem.write`) do not allow arbitrary host access. They dynamically resolve paths against a safe workspace root (e.g., `/tmp/mycel_workspace/{workspace_id}`) and reject path traversal attempts (e.g., `../../`).

### Artifact References
To prevent LLM context windows from being overwhelmed by massive binary outputs (like 50MB videos or 10MB PDFs), tools that generate large outputs return an `ArtifactReference`. This struct contains metadata and secure URLs, keeping the actual binary payload out of the prompt.
