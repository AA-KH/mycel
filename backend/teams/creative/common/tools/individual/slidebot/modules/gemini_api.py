"""
Gemini API Module - Encapsulates all Gemini API calls
"""

import os
import io
import json
import base64
import time
import asyncio
import requests
from pathlib import Path
from typing import Optional, List
from PIL import Image

from .config import GEMINI_API_BASE, GEMINI_API_KEY, MAX_RETRIES, RETRY_DELAY


# ============ Utility Functions ============

def get_image_base64(image_path: str) -> str:
    """Convert image to base64 encoding"""
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string


def get_image_mime_type(image_path: str) -> str:
    """Get the MIME type of an image"""
    ext = Path(image_path).suffix.lower()
    mime_types = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.webp': 'image/webp',
    }
    return mime_types.get(ext, 'image/png')


def parse_json_from_text(text: str) -> Optional[dict]:
    """Parse JSON from text"""
    try:
        json_start = text.find('```json')
        if json_start != -1:
            json_start = text.find('\n', json_start) + 1
            json_end = text.find('```', json_start)
            if json_end != -1:
                json_str = text[json_start:json_end].strip()
                return json.loads(json_str)

        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = text[json_start:json_end]
            return json.loads(json_str)

    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")

    return None


# ============ Text Generation ============

def _generate_text_sync(prompt: str, thinking_level: str = "high") -> tuple[str, str]:
    """
    Synchronous version of text generation (internal function, executed in a thread pool)
    
    Returns: (generated text, retry info message)
    """
    url = f"{GEMINI_API_BASE}/gemini-3-pro-preview:generateContent"

    payload = {
        "model": "gemini-3-pro-preview",
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "thinkingConfig": {
                "thinkingLevel": thinking_level
            }
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY,
    }

    retry_info = ""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[Text Gen] Attempt {attempt}...")
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            print(f"Text Gen Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                # Parse response, extract text
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                if attempt > 1:
                                    retry_info = f"⚠️ API unstable, succeeded after {attempt} retries"
                                return part["text"], retry_info
                print(f"Abnormal response format: {result}")
                last_error = "Abnormal response format"
            else:
                print(f"Text gen failed: {response.text}")
                last_error = f"API returned error: {response.status_code}"

        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            print(f"[Text Gen] Attempt {attempt} timed out")
        except requests.exceptions.ConnectionError:
            last_error = "Network connection error"
            print(f"[Text Gen] Attempt {attempt} connection error")
        except Exception as e:
            last_error = str(e)
            print(f"[Text Gen] Attempt {attempt} error: {e}")

        # Wait before retrying if not the last attempt
        if attempt < MAX_RETRIES:
            print(f"[Text Gen] Waiting {RETRY_DELAY} seconds before retry...")
            time.sleep(RETRY_DELAY)

    # All retries failed
    retry_info = f"❌ API call failed (retried {MAX_RETRIES} times): {last_error}"
    return "", retry_info


async def generate_text(prompt: str, thinking_level: str = "high") -> tuple[str, str]:
    """
    Asynchronous version of text generation (uses thread pool to avoid blocking the event loop)
    
    Returns: (generated text, retry info message)
    """
    # Execute synchronous HTTP request in thread pool to avoid blocking event loop
    return await asyncio.to_thread(_generate_text_sync, prompt, thinking_level)


# ============ Image Generation ============

def _generate_ppt_image_sync(prompt: str, output_path: Path, reference_image_path: Optional[str] = None, custom_logo_path: Optional[str] = None, reference_type: str = "reference", template_analysis: Optional[dict] = None, page_materials: Optional[List[dict]] = None) -> tuple[bool, str]:
    """
    Synchronous version of PPT image generation (internal function, executed in a thread pool)
    
    Args:
        page_materials: Page materials list [{type, path, filename, description}, ...]
    
    Returns: (success boolean, retry info message)
    """
    # Logo image path - only process if user uploaded a custom logo
    LOGO_PATH = None
    if custom_logo_path and os.path.exists(custom_logo_path):
        LOGO_PATH = Path(custom_logo_path)
        print(f"Using custom Logo: {LOGO_PATH}")
    else:
        print("No Logo uploaded, skipping Logo processing")
    
    url = f"{GEMINI_API_BASE}/gemini-3-pro-image-preview:generateContent"

    retry_info = ""
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[Image Gen] Attempt {attempt}...")

            # Check for images
            has_logo = LOGO_PATH is not None and LOGO_PATH.exists()
            has_reference = reference_image_path and os.path.exists(reference_image_path)

            # Build full prompt including all image instructions
            full_prompt = prompt

            if has_logo:
                full_prompt += """

[NOTE] The attached images include a company logo uploaded by the user. Please place this logo in the top right corner of the generated image, maintaining its clarity and completeness."""

            if has_reference:
                if reference_type == "template":
                    # Template mode: strict adherence
                    full_prompt += """

[HIGHEST PRIORITY - PPT Template Design Guidelines]
The attachments contain a user-uploaded PPT master template image. This is a design template that MUST be strictly followed.
The generated PPT page must completely match the visual style of the master template, ignoring any other color or font settings."""
                    
                    # Add specific parameters if analysis results exist
                    if template_analysis:
                        colors = template_analysis.get("colors", {})
                        fonts = template_analysis.get("fonts", {})
                        layout = template_analysis.get("layout", {})
                        background = template_analysis.get("background", {})
                        style_summary = template_analysis.get("style_summary", "")
                        
                        full_prompt += f"""

[Template Analysis Results - MUST STRICTLY EXECUTE]

■ Color Scheme (MUST use these exact color values):
  - Background: {colors.get('background', 'As per template')}
  - Primary (Main Title): {colors.get('primary', 'As per template')}
  - Secondary (Subtitles): {colors.get('secondary', 'As per template')}
  - Accent (Highlights): {colors.get('accent', 'As per template')}
  - Primary Text: {colors.get('text_primary', 'As per template')}
  - Secondary Text: {colors.get('text_secondary', 'As per template')}

■ Typography Guidelines:
  - Title: {fonts.get('title_style', 'Bold')}, approx {fonts.get('title_size', '48pt')}
  - Body: {fonts.get('body_style', 'Regular')}, approx {fonts.get('body_size', '14pt')}

■ Layout Structure:
  - Title Position: {layout.get('title_position', 'As per template')}
  - Content Area: {layout.get('content_area', 'As per template')}
  - Has Header: {'Yes' if layout.get('has_header') else 'No'}
  - Has Footer: {'Yes' if layout.get('has_footer') else 'No'}

■ Background Design:
  - Background Type: {background.get('type', 'As per template')}
  - Background Description: {background.get('description', 'As per template')}
  - Decorative Elements: {background.get('decoration_description', 'None') if background.get('has_decorations') else 'None'}

■ Overall Style: {style_summary}

Please strictly follow the above guidelines to ensure the generated image looks like a different page from the exact same PPT template.

[SPECIAL EMPHASIS] If the master template contains background images, patterns, or decorative elements, you MUST retain and replicate these background designs during generation, ensuring every page has a background effect consistent with the master template."""
                    else:
                        full_prompt += """

Please carefully observe the following in the master template image:
1. Precise color scheme (specific color values for background, title, body, and accents)
2. Font style and size proportions
3. Layout position of title and content
4. Background design (solid color/gradient/image/decorative elements)
5. Overall visual style and professionalism

The generated image must be highly consistent visually with the master template, looking like a different page of the same template.

[SPECIAL EMPHASIS] If the master template contains background images, patterns, or decorative elements, you MUST retain and replicate these background designs during generation, ensuring every page has a background effect consistent with the master template."""
                elif reference_type == "refine":
                    # Refine mode: fine-tune based on currently generated image
                    full_prompt += """

[REFINE MODE - HIGHEST PRIORITY]
The attachments contain the currently generated PPT page image, which serves as the baseline for refinement.
Please strictly adhere to the following principles:

⚠️ Core Requirements:
1. Keep the overall layout structure of the current image unchanged
2. Keep the color scheme of the current image unchanged
3. Keep the font style of the current image unchanged
4. Only make local adjustments based on the user's specific modification feedback
5. Parts not explicitly requested to be changed by the user must remain as is

Please make only the user-requested fine-tuning based on the reference image, ensuring the generated image maintains a high degree of visual consistency with the original image."""
                else:
                    # Normal reference mode
                    full_prompt += """

[ALSO] The attachments contain a reference image uploaded by the user. When generating the result image, please try to reference the color scheme, font, and style of this reference image."""

            # Build parts list
            parts = [{"text": full_prompt}]

            # Add logo image (only if user uploaded a custom logo)
            if has_logo:
                logo_base64 = get_image_base64(str(LOGO_PATH))
                logo_mime = get_image_mime_type(str(LOGO_PATH))
                parts.append({
                    "inline_data": {
                        "mime_type": logo_mime,
                        "data": logo_base64
                    }
                })
                print(f"Loaded logo image: {LOGO_PATH}")

            # Add extra reference image
            if has_reference:
                ref_base64 = get_image_base64(reference_image_path)
                ref_mime = get_image_mime_type(reference_image_path)
                parts.append({
                    "inline_data": {
                        "mime_type": ref_mime,
                        "data": ref_base64
                    }
                })
                print(f"Loaded reference image: {reference_image_path}, Type: {reference_type}")

            # Add page materials
            if page_materials:
                images_added = 0
                image_descriptions = []
                table_texts = []
                
                for i, material in enumerate(page_materials):
                    material_type = material.get("type", "image")
                    material_desc = material.get("description", "")
                    
                    if material_type == "image":
                        # Image material: add to inline_data
                        material_path = material.get("path")
                        if material_path and os.path.exists(material_path):
                            try:
                                material_base64 = get_image_base64(material_path)
                                material_mime = get_image_mime_type(material_path)
                                parts.append({
                                    "inline_data": {
                                        "mime_type": material_mime,
                                        "data": material_base64
                                    }
                                })
                                images_added += 1
                                # Collect image descriptions
                                if material_desc:
                                    image_descriptions.append(f"Image {images_added}: {material_desc}")
                                print(f"Loaded image material {i+1}: {material.get('filename')} - {material_desc or 'No description'}")
                            except Exception as e:
                                print(f"Failed to load image material {material.get('filename')}: {e}")
                    
                    elif material_type in ["table", "table_text"]:
                        # Table material: add to prompt text
                        table_text = material.get("table_text", "")
                        if table_text:
                            table_header = f"[Table: {material.get('filename')}]"
                            if material_desc:
                                table_header += f"\nDescription: {material_desc}"
                            table_texts.append(f"{table_header}\n{table_text}")
                            print(f"Loaded table material {i+1}: {material.get('filename')} - {material_desc or 'No description'}")
                
                # Build material instructions
                material_prompts = []
                
                if images_added > 0:
                    image_desc_text = ""
                    if image_descriptions:
                        image_desc_text = "\nUser descriptions for images:\n" + "\n".join(image_descriptions)
                    material_prompts.append(f"""
[USER UPLOADED IMAGE MATERIALS - HIGHEST PRIORITY]
The attachments contain {images_added} user-uploaded image materials (possibly charts, screenshots, etc.). {image_desc_text}
You MUST:
1. Directly copy/embed these image materials into the generated PPT page
2. Maintain the original content, proportions, and clarity of the materials
3. Do not summarize, redraw, or simplify the image materials
4. The image materials should serve as core content elements for the page, arrange the layout reasonably
5. Understand the purpose and meaning of the images based on the user's descriptions""")
                
                if table_texts:
                    # Combine table texts, limit total length
                    combined_table_text = chr(10).join(table_texts)
                    if len(combined_table_text) > 3000:
                        combined_table_text = combined_table_text[:3000] + "\n...(Table data too long, truncated to first 3000 chars)"
                    
                    material_prompts.append(f"""
[USER UPLOADED TABLE DATA - HIGHEST PRIORITY]
The following is the table data the user specified to display on this page. You MUST:
1. Present the table data completely and accurately in the PPT page
2. You may convert the table data into aesthetic table graphics, charts, or data visualizations
3. Maintain data accuracy, do not modify or omit data
4. Choose an appropriate visualization method based on the table content and user description (table, bar chart, pie chart, line chart, etc.)

{combined_table_text}""")
                
                if material_prompts:
                    full_prompt += "\n".join(material_prompts)
                    # Update prompt in parts
                    parts[0] = {"text": full_prompt}

            print(f"Final prompt length: {len(full_prompt)}, Attachments count: {len(parts) - 1}, Template mode: {reference_type == 'template'}")

            # Build request payload
            payload = {
                "model": "gemini-3-pro-image-preview",
                "contents": [
                    {
                        "parts": parts
                    }
                ],
                "generationConfig": {
                    "responseModalities": ["TEXT", "IMAGE"],
                    "imageConfig": {
                        "aspectRatio": "16:9",
                        "imageSize": "4K"
                    }
                }
            }

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY
            }

            # Send request
            response = requests.post(url, json=payload, headers=headers, timeout=180)
            print(f"Image gen Status Code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                # Parse response, extract image
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            # Process image response
                            if "inlineData" in part:
                                image_data = part["inlineData"]["data"]
                                # Decode base64 and save image
                                image_bytes = base64.b64decode(image_data)
                                
                                # Compress image to speed up frontend loading
                                try:
                                    img = Image.open(io.BytesIO(image_bytes))
                                    # Convert to RGB (if RGBA)
                                    if img.mode == 'RGBA':
                                        # Create white background
                                        background = Image.new('RGB', img.size, (255, 255, 255))
                                        background.paste(img, mask=img.split()[3])
                                        img = background
                                    elif img.mode != 'RGB':
                                        img = img.convert('RGB')
                                    
                                    # Save as JPEG format, quality 85%, file size approx 500KB-1MB
                                    output_path_jpg = str(output_path).replace('.png', '.jpg')
                                    img.save(output_path_jpg, 'JPEG', quality=85, optimize=True)
                                    print(f"Image compressed and saved: {output_path_jpg} (Original PNG -> JPEG)")
                                    
                                    # Update output path to jpg
                                    if attempt > 1:
                                        retry_info = f"⚠️ API unstable, succeeded after {attempt} retries"
                                    return True, retry_info
                                except Exception as compress_err:
                                    print(f"Image compression failed, using original format: {compress_err}")
                                    # If compression fails, save original PNG
                                    with open(output_path, "wb") as f:
                                        f.write(image_bytes)
                                    print(f"Image saved: {output_path}")
                                    if attempt > 1:
                                        retry_info = f"⚠️ API unstable, succeeded after {attempt} retries"
                                    return True, retry_info

                print(f"No image found in response")
                last_error = "No image found in response"
            else:
                print(f"Image gen failed: {response.status_code}")
                last_error = f"API returned error: {response.status_code}"

        except requests.exceptions.Timeout:
            last_error = "Request timeout"
            print(f"[Image Gen] Attempt {attempt} timed out")
        except requests.exceptions.ConnectionError:
            last_error = "Network connection error"
            print(f"[Image Gen] Attempt {attempt} connection error")
        except Exception as e:
            last_error = str(e)
            print(f"[Image Gen] Attempt {attempt} error: {e}")
            import traceback
            traceback.print_exc()

        # Wait before retrying if not the last attempt
        if attempt < MAX_RETRIES:
            print(f"[Image Gen] Waiting {RETRY_DELAY} seconds before retry...")
            time.sleep(RETRY_DELAY)

    # All retries failed
    retry_info = f"❌ Image generation failed (retried {MAX_RETRIES} times): {last_error}"
    return False, retry_info


async def generate_ppt_image(prompt: str, output_path: Path, reference_image_path: Optional[str] = None, custom_logo_path: Optional[str] = None, reference_type: str = "reference", template_analysis: Optional[dict] = None, page_materials: Optional[List[dict]] = None) -> tuple[bool, str]:
    """
    Asynchronous version of PPT image generation (uses thread pool to avoid blocking the event loop)
    
    Args:
        page_materials: Page materials list [{type, path, filename, description}, ...]
    
    Returns: (success boolean, retry info message)
    """
    # Execute synchronous HTTP request in thread pool to avoid blocking event loop
    return await asyncio.to_thread(
        _generate_ppt_image_sync, 
        prompt, 
        output_path, 
        reference_image_path, 
        custom_logo_path, 
        reference_type, 
        template_analysis,
        page_materials
    )


# ============ Template Analysis ============

def analyze_template_design(image_path: str) -> dict:
    """
    Use AI to analyze master template image, extract design guidelines
    Returns: Dictionary containing parameters like color scheme, font, layout, etc.
    """
    print(f"[Template Analysis] Starting analysis: {image_path}")
    
    try:
        # Get image data
        image_base64 = get_image_base64(image_path)
        image_mime = get_image_mime_type(image_path)
        
        # Optimized Prompt
        analysis_prompt = """You are a professional PPT design analyst.
Please output JSON data directly, strictly forbidding any opening remarks, thought processes, Markdown tags, or summaries.

The returned JSON structure MUST be as follows:
{
    "colors": {
        "background": "#FFFFFF",
        "primary": "#000000",
        "secondary": "#000000", 
        "accent": "#000000",
        "text_primary": "#000000",
        "text_secondary": "#000000"
    },
    "fonts": {
        "title_style": "Font style description",
        "title_size": "Font size estimation",
        "body_style": "Body font style description",
        "body_size": "Body font size estimation"
    },
    "layout": {
        "title_position": "Title position description",
        "content_area": "Content area description",
        "has_header": true,
        "has_footer": true,
        "has_sidebar": false
    },
    "background": {
        "type": "Solid/Gradient/Image/Pattern",
        "description": "Detailed description",
        "has_decorations": true,
        "decoration_description": "Decoration description"
    },
    "style_summary": "Overall style summary"
}

Requirements:
1. Colors must be valid 6-character hex codes (#RRGGBB).
2. Must answer in English.
3. Strictly follow the JSON format."""

        url = f"{GEMINI_API_BASE}/gemini-3-pro-preview:generateContent"
        
        payload = {
            "model": "gemini-3-pro-preview",
            "contents": [{
                "parts": [
                    {"text": analysis_prompt},
                    {
                        "inline_data": {
                            "mime_type": image_mime,
                            "data": image_base64
                        }
                    }
                ]
            }],
            # Critical Config: Force JSON output mode
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=3600)
        
        if response.status_code == 200:
            result = response.json()
            # Extract text content - Note: parts[1] is actual response, parts[0] might be thinking
            raw_text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[1].get("text", "")
            
            # --- Robust parsing logic ---
            # 1. Try direct parsing
            try:
                analysis = json.loads(raw_text)
            except json.JSONDecodeError:
                # 2. If parsing fails, try regex extraction (prevents AI from returning Markdown tags or chatter)
                import re
                json_match = re.search(r'\{[\s\S]*\}', raw_text)
                if json_match:
                    clean_content = json_match.group()
                    # Remove potential JSON internal comments (common error cause)
                    clean_content = re.sub(r'//.*', '', clean_content) 
                    analysis = json.loads(clean_content)
                else:
                    raise ValueError("Could not find valid JSON structure in response")

            print(f"[Template Analysis] Analysis successful: {analysis.get('style_summary', 'No summary')}")
            return analysis
        
        else:
            print(f"[Template Analysis] API call failed: {response.status_code}, {response.text}")
            return None
            
    except Exception as e:
        print(f"[Template Analysis] Exception occurred: {str(e)}")
        return None
