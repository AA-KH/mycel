# Cloudinary Integration

Cloudinary serves as the primary `StorageProvider` for Mycel, handling remote persistence, format transformations, and CDN delivery for generated artifacts.

## Configuration
Cloudinary relies on credentials specified in `backend/core/config.py`:
- `CLOUDINARY_CLOUD_NAME`
- `CLOUDINARY_API_KEY`
- `CLOUDINARY_API_SECRET`

**Security Boundary**: These credentials are NEVER exposed to the LLM, the AgentRuntime, or the frontend API. They remain strictly within the `CloudinaryStorageProvider` module.

## Folder Strategy
Artifacts are uploaded to highly deterministic, tenant-aware paths:
`mycel/companies/{company_id}/tasks/{task_id}/{artifact_id}_{filename}`

This ensures multi-tenant isolation and prevents path collision.

## Resource Types
Cloudinary distinguishes between `image`, `video`, and `raw` resource types. The `CloudinaryStorageProvider` automatically maps Mycel artifact types:
- `video`, `audio` -> `video` (Cloudinary handles audio via the video resource type)
- `image` -> `image`
- `document`, `pdf`, `text` -> `raw`

## Error Handling
If Cloudinary throws a timeout or transient error, the `ArtifactService` marks the artifact as `FAILED`. In a full system with Celery or RabbitMQ, these can be retried using bounded exponential backoff.
