# Knowledge Provider Model

To support rapid scaling and testing, the Knowledge System relies entirely on abstract interfaces rather than concrete third-party SDKs. 

## Embedding Provider
Defined in `knowledge/retrieval/embedding.py`.
- **Interface**: `EmbeddingProvider`
- **TOS 4 Implementation**: `MockEmbeddingProvider` (Generates deterministic mock vectors).
- **Future Implementations**: `OpenAIEmbeddingProvider`, `HuggingFaceEmbeddingProvider`, `VertexAIEmbeddingProvider`.

## Vector Store
Defined in `knowledge/retrieval/vectorstore.py`.
- **Interface**: `VectorStore`
- **TOS 4 Implementation**: `InMemoryVectorStore` (Stores vectors in memory dictionaries partitioned by `knowledge_space_id`).
- **Future Implementations**: `FAISSVectorStore`, `MongoDBVectorSearchStore`, `QdrantVectorStore`.

## Parsers
Defined in `knowledge/ingestion/parser.py`.
- **Interface**: `DocumentParser`
- **TOS 4 Implementation**: `MockTextParser` (Echoes back the URI for testing).
- **Future Implementations**: `PDFMinerParser`, `BeautifulSoupParser`, `UnstructuredIOProvider`.
