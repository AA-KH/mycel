# Tool Catalog

The following tools are currently implemented and registered in the Mycel Tool System.

## System Tools
- **mock.success**: Always succeeds, used for testing.
- **mock.error**: Always fails, used for testing.

## Web & Research
- **web.search**: Searches the web. Input requires `query`. Requires network access.
- **browser.open**: Opens a URL and extracts its content securely, enforcing SSRF protections.
- **web.scrape**: Scrapes structured data from a URL.

## Filesystem
- **filesystem.read**: Reads a file within the strictly enforced workspace sandbox.
- **filesystem.write**: Writes a file within the workspace sandbox.

## Media
- **ffmpeg**: Executes structured FFmpeg operations (e.g., resize, trim) rather than raw arbitrary commands. High risk.
- **cloudinary.upload**: Uploads an artifact to Cloudinary and returns a secure `ArtifactReference`. Prevents API keys from entering the LLM prompt.
