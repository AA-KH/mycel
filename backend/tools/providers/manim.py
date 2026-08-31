import os
import subprocess
import tempfile
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ManimProviderError(Exception):
    pass

class ManimProvider:
    """
    Native integration of Manim execution for technical animations.
    Runs Manim in a controlled subprocess.
    """
    
    @staticmethod
    async def render(code: str, scene_class: str = "Scene1", resolution: str = "720p") -> bytes:
        """
        Render Manim code to an MP4 video and return its bytes.
        """
        # Create a temporary directory for isolation
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = os.path.join(tmpdir, "scene.py")
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            
            # Map resolution string to manim flags
            res_flag = "-ql"  # 480p 15fps
            if resolution == "720p":
                res_flag = "-qm"  # 720p 30fps
            elif resolution == "1080p":
                res_flag = "-qh"  # 1080p 60fps
                
            cmd = ["manim", script_path, scene_class, res_flag, "--media_dir", tmpdir, "-o", "output.mp4"]
            
            logger.info(f"Running Manim: {' '.join(cmd)}")
            
            # Run manim as a subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tmpdir
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Manim render failed: {stderr.decode('utf-8', errors='ignore')}")
                raise ManimProviderError(f"Manim rendering failed with exit code {process.returncode}:\n{stderr.decode('utf-8', errors='ignore')}")
            
            # Find the rendered video file
            output_file = None
            for root, _, files in os.walk(tmpdir):
                if "output.mp4" in files:
                    output_file = os.path.join(root, "output.mp4")
                    break
                    
            if not output_file or not os.path.exists(output_file):
                logger.error(f"Manim output file not found in {tmpdir}")
                logger.debug(f"Stdout: {stdout.decode('utf-8', errors='ignore')}")
                raise ManimProviderError("Manim output video not found after successful exit.")
                
            with open(output_file, "rb") as f:
                video_bytes = f.read()
                
            return video_bytes

def get_manim_provider() -> ManimProvider:
    return ManimProvider()
