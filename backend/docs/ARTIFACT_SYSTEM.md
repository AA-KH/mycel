# Artifact System

The Artifact System in Mycel is responsible for managing the complete lifecycle, identity, validation, and storage of any physical deliverables produced by AI Employees (e.g., images, videos, audio files, PDFs).

## Core Philosophy
An LLM response is not the same as a Task Completion. If a user asks for a promotional video, Mycel will not mark the task complete unless a valid `video/mp4` file actually exists in storage, is properly typed, and belongs to the correct company workspace. 

**Cloudinary is NOT the Artifact System.** Cloudinary is simply one possible `StorageProvider`. Mycel owns the artifact identity, the MIME type validation, the storage orchestration, and the delivery representation.

## Architecture

1. **Artifact Model**: Represents the canonical database record. It contains:
   - `artifact_id` (e.g., `art_...`)
   - `company_id` and `workspace_id`
   - `type` and `mime_type`
   - `status` (CREATED, UPLOADING, VALIDATING, READY, FAILED)
   - `storage_provider` and `storage_key`
   - `parent_artifact_id` (Lineage)

2. **Artifact Service**: Orchestrates the entire creation lifecycle:
   - Registers the initial record as `CREATED`.
   - Calls the appropriate `BaseValidator` (e.g., `VideoValidator`) to ensure the generated file matches the expected output.
   - Calculates a SHA-256 checksum for integrity and future deduplication.
   - Delegates to a `StorageProvider` for upload.
   - Updates the status to `READY`.

3. **Storage Providers**:
   - `StorageProvider` interface abstracts away `upload`, `delete`, and `exists`.
   - `CloudinaryStorageProvider` maps artifacts to Cloudinary using isolated tenant paths (`mycel/companies/{company}/...`).
   - `MockStorageProvider` is used for local tests without network dependencies.

4. **AgentRuntime Integration**:
   - `CoreResultVerifier` intercepts the end of a task execution.
   - If the task's expected output was an artifact (e.g., `video`), it queries the ArtifactService to ensure the `artifact_id` exists, belongs to the company, and is actually `READY`.

## Lineage and Versioning
An artifact can reference a `parent_artifact_id`. This allows us to trace the origins of a file. For example, if an AI generates an Audio file, and then uses FFmpeg to merge it with an Image file, the resulting Video file will have a lineage tracing back to the audio and image artifacts.
