# Tool Access Model

The overall Tool Access Model inside Mycel is hierarchical and additive. Phase TOS 3 implements only the foundational layer: **Team Common Tools**.

The effective permissions of an individual agent during execution will be resolved by flattening a hierarchy of grants and restrictions.

## Future Access Composition
The effective tool permissions of an Agent will be determined by:

1. **Team Common Tools** *(Implemented in TOS 3)*
   - The pool of tools generally available to the entire domain.
2. **Position Tools** *(Future)*
   - Role-specific tool grants.
3. **Employee Tool Grants** *(Future)*
   - Specific tools explicitly granted to the individual agent.
4. **Task Restrictions** *(Future)*
   - Dynamic restrictions applied to a specific task (e.g., "disable filesystem tools for this untrusted task").
5. **Security Policy** *(Future)*
   - Global risk-based rules (e.g., "critical risk tools require human approval").

### Effective Tool Access
`Effective Tools = ((Team Pool) + (Position Pool) + (Employee Grants)) - (Task Restrictions) * (Security Policy)`

This model allows Mycel to separate *what the company provides* (Team/Position) from *what the agent is trusted with* (Employee/Task).
