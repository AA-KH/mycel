# Arjun Toolchain

Arjun Singh has access to a specialized toolchain natively integrated into the Mycel Security Gateway.

## Tools Registered

1. **`creative.technical_animation.render`**
   - **Provider**: `ManimProvider`
   - **Purpose**: Compiles LLM-generated Python (Manim) code into a video asset.
   - **Security**: Runs in a sandboxed TemporaryDirectory subprocess. Output path is resolved securely via Artifact Storage.

2. **`creative.stock_media.search`**
   - **Provider**: `StockMediaProvider` (adapted from Pexels client)
   - **Purpose**: Sources generic high-quality video and image backgrounds for compositions.

3. **`creative.speech.generate`**
   - **Provider**: `TTSProvider`
   - **Purpose**: Generates high-fidelity voiceovers for promotional material.

4. **`media.ffmpeg`**
   - **Provider**: `FFmpegProvider` (existing)
   - **Purpose**: Serves as the composition engine to stitch, overlay, and encode final renders.
