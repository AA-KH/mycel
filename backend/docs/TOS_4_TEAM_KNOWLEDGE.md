# TOS 4: Team Knowledge System

## Overview
The Team Knowledge System defines **"What information does this Team have access to when solving problems?"**. It establishes a strictly scoped RAG (Retrieval-Augmented Generation) foundation for every team in Mycel.

## Core Entities
1. **KnowledgeSpace**: A bounded container for a team's domain knowledge. A team has exactly one active space.
2. **KnowledgeSource**: The conceptual origin of information (e.g. `web_page`, `document`, `api`). It possesses a `trust_level` which can be used later to weigh search results.
3. **KnowledgeDocument**: A logical entity parsed from a source. Tracks `version`, `checksum`, and indexing `status`.
4. **KnowledgeChunk**: Textual segments embedded and pushed to a Vector Store.

## Why Knowledge is Separated from Reasoning
Mycel strictly decouples *Information Retrieval* from *Reasoning*.
- **Knowledge System**: Ingests, parses, embeds, and searches. It returns a structured `KnowledgeContext` (with chunks, references, and citations).
- **Reasoning Engine**: Consumes this context to synthesize answers. The Knowledge System **does not evaluate or reason about the content**.

## Why Knowledge is Separated from Tools and Artifacts
- **Tools**: Perform actions (e.g. `web.scrape`). A tool might fetch data, but it is the Knowledge System that turns that data into searchable embeddings.
- **Artifacts**: The Artifact System stores physical outputs (PDFs, videos). If a team uploads a document, the Artifact System holds the file in Cloudinary, while the Knowledge System parses and chunks it for RAG.
