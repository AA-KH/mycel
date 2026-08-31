# Team Knowledge Security

Security and strict cross-team isolation are paramount in the Mycel Knowledge System.

## The Isolation Rule
A Team **MUST NOT** retrieve knowledge belonging to another Team unless explicitly granted via a future Shared Knowledge capability.

## Enforcement Mechanism
Isolation is not left to chance or client-side filtering. It is enforced server-side within the `KnowledgeRetriever` and `KnowledgeAccessPolicy`.

1. **The Request**: A caller requests search for a specific `team_id`.
2. **The Resolution**: The `KnowledgeRegistry` resolves that `team_id` to its singular, authorized `knowledge_space_id`.
3. **The Restriction**: If a caller attempts to bypass this by providing a foreign `knowledge_space_id`, the `KnowledgeAccessPolicy` strictly rejects the request.
4. **The Search**: The `VectorStore` requires `knowledge_space_id` as a mandatory argument for `similarity_search`, physically partitioning the result set.

*(See `tests/knowledge/test_knowledge_system.py::test_team_isolation_rejection` for the automated enforcement of this boundary).*
