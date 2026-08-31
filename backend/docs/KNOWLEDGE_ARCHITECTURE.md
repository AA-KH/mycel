# Knowledge Architecture

## The Ingestion Pipeline
The `IngestionService` orchestrates the transformation of unstructured data into searchable vectors.

1. **Source -> Document**: A `KnowledgeSource` creates a `KnowledgeDocument` with a `PENDING` status.
2. **Parser**: The `DocumentParser` abstraction extracts plain text from the source URI (e.g. parsing a PDF, downloading HTML).
3. **Chunker**: The `ChunkingService` breaks the text into manageable `KnowledgeChunk` entities.
4. **Embedding**: The `EmbeddingProvider` interface converts chunks into dense vector representations.
5. **Vector Store**: The `VectorStore` interface persists the vectors, **keyed securely by the `knowledge_space_id`**.
6. **Completion**: Document status updates to `INDEXED`.

## The Retrieval Pipeline
The `KnowledgeRetriever` provides a secure, abstracted search mechanism.

1. **Access Resolution**: Validates the requesting `team_id` has an active `KnowledgeSpace`.
2. **Query Embedding**: Converts the search query to a vector.
3. **Similarity Search**: Queries the Vector Store, strictly filtering by `knowledge_space_id`.
4. **Context Construction**: Returns a `KnowledgeContext` containing lightweight `KnowledgeReference` objects and the raw `retrieved_chunks` for the Reasoning Engine.
