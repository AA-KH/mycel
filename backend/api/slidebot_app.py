"""
PPT AI Generator - Backend API Service
Strictly implement according to product flow
"""

import os
import re
import time
import zipfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from core.logger import logger

# Modify imports to use the correct path in agent-virtual-office
from teams.creative.common.tools.individual.slidebot.modules.config import (
    XFYUN_APPID,
    XFYUN_SECRET_KEY,
    OUTPUT_DIR,
    REFERENCE_DIR,
    AUDIO_DIR,
    MATERIALS_DIR,
    SUPPORT_DOCS_DIR,
    FRONTEND_BUILD_DIR,
    LOGIN_RECORDS_FILE
)
from teams.creative.common.tools.individual.slidebot.modules.prompts import (
    OUTLINE_PROMPT_TEMPLATE,
    DEFAULT_DESIGN_PRINCIPLES,
    REFINE_OUTLINE_PROMPT,
    STYLE_GENERATION_PROMPT,
    REFINE_STYLE_PROMPT,
    REFINE_PAGE_PROMPT,
    build_color_scheme_spec,
    build_font_scheme_spec
)
from teams.creative.common.tools.individual.slidebot.modules.models import (
    LoginRequest,
    UserInputRequest,
    RefineRequest,
    GenerateImageRequest,
    GenerateAllImagesRequest,
    BaseRequest,
    RefinePageRequest,
    OutlineUpdateRequest
)
from teams.creative.common.tools.individual.slidebot.modules.asr import XfyunASR, parse_xfyun_result, format_dialogue_as_text
from teams.creative.common.tools.individual.slidebot.modules.invite_codes import (
    load_invite_codes,
    verify_invite_code,
    record_login,
    get_login_records_from_csv
)
from teams.creative.common.tools.individual.slidebot.modules.session import SessionStage, get_session, add_message
from teams.creative.common.tools.individual.slidebot.modules.gemini_api import (
    parse_json_from_text,
    generate_text,
    generate_ppt_image,
    analyze_template_design
)
from teams.creative.common.tools.individual.slidebot.modules.visit_counter import get_visit_count, increment_visit_count
from teams.creative.common.tools.individual.slidebot.modules.doc_extract import extract_text_from_document, extract_table_from_file

# ============ FastAPI App ============

slidebot_app = FastAPI(
    title="PPT AI API",
    description="SlideBot API",
    version="2.0.0"
)

# CORS Configuration
slidebot_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Health Check and Default Config ============

@slidebot_app.get("/api/health")
async def root():
    return {
        "message": "PPT API is running",
        "version": "2.0.0",
        "docs": "/docs"
    }


@slidebot_app.get("/api/defaults")
async def get_defaults():
    return {
        "design_principles": DEFAULT_DESIGN_PRINCIPLES
    }


# ============ Login Validation ============

@slidebot_app.post("/api/login")
async def login(request: LoginRequest):
    code = request.invite_code.strip()
    if not code:
        return {"success": False, "message": "No code"}

    if verify_invite_code(code):
        record_login(code)
        return {"success": True, "message": "Success", "invite_code": code.upper()}
    else:
        return {"success": False, "message": "Invalid"}


@slidebot_app.get("/api/login/records")
async def get_login_records():
    records = get_login_records_from_csv()
    data = load_invite_codes()
    return {
        "total_codes": len(data.get("codes", [])),
        "total_logins": len(records),
        "records": records[-50:],
        "csv_file": str(LOGIN_RECORDS_FILE)
    }


@slidebot_app.get("/api/login/records/download")
async def download_login_records():
    if not LOGIN_RECORDS_FILE.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path=LOGIN_RECORDS_FILE, filename="login_records.csv", media_type="text/csv")


# ============ Session Management ============

@slidebot_app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    session = get_session(session_id)
    return {
        "session_id": session_id,
        "stage": session["stage"],
        "outline": session["outline_json"],
        "style": session["style_json"],
        "images": session["generated_images"],
        "messages": session["messages"],
        "audio_transcript": session.get("audio_transcript", "")
    }


# ============ Audio Upload and ASR Transcription ============

@slidebot_app.post("/api/audio/upload")
async def upload_audio(
    session_id: str = Form(...),
    num_speaker: Optional[int] = Form(None),
    file: UploadFile = File(...)
):
    session = get_session(session_id)
    file_ext = Path(file.filename).suffix or '.mp3'
    audio_path = AUDIO_DIR / f"{session_id}_audio{file_ext}"

    with open(audio_path, "wb") as f:
        content = await file.read()
        f.write(content)

    logger.info(f"Audio saved: {audio_path}")

    try:
        asr = XfyunASR(appid=XFYUN_APPID, secret_key=XFYUN_SECRET_KEY, upload_file_path=str(audio_path))
        result = asr.get_result(num_speaker)
        dialogue_list = parse_xfyun_result(result)

        if dialogue_list:
            transcript_text = format_dialogue_as_text(dialogue_list)
            session["audio_transcript"] = transcript_text
            add_message(session_id, "assistant", f"ASR done.\\n\\n{transcript_text}")
            return {"success": True, "message": "Success", "transcript": transcript_text, "dialogue_count": len(dialogue_list)}
        else:
            return {"success": False, "message": "Empty", "transcript": ""}
    except Exception as e:
        logger.error(f"ASR error: {e}")
        return {"success": False, "message": f"Error: {str(e)}", "transcript": ""}


@slidebot_app.get("/api/audio/transcript/{session_id}")
async def get_audio_transcript(session_id: str):
    session = get_session(session_id)
    return {"success": True, "transcript": session.get("audio_transcript", "")}


# ============ Support Doc Upload ============

@slidebot_app.post("/api/support-doc/upload")
async def upload_support_document(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    session = get_session(session_id)
    allowed_extensions = ['.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls', '.txt']
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return {"success": False, "message": f"Not supported: {file_ext}"}
    
    file_path = SUPPORT_DOCS_DIR / f"{session_id}_{int(time.time())}_{file.filename}"
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"Doc saved: {file_path}")
    extracted_text = extract_text_from_document(str(file_path), file.filename)
    
    if not extracted_text:
        return {"success": False, "message": "Extraction failed"}
    
    if len(extracted_text) > 10000:
        extracted_text = extracted_text[:10000] + "\\n...(truncated)"
    
    session["support_docs_files"].append({
        "filename": file.filename,
        "path": str(file_path),
        "text_length": len(extracted_text)
    })
    
    if session["support_docs_text"]:
        session["support_docs_text"] += f"\\n\\n--- {file.filename} ---\\n{extracted_text}"
    else:
        session["support_docs_text"] = f"--- {file.filename} ---\\n{extracted_text}"
    
    add_message(session_id, "assistant", f"Doc {file.filename} uploaded.")
    return {"success": True, "message": "Success", "filename": file.filename, "text_length": len(extracted_text), "text_preview": extracted_text[:500]}


@slidebot_app.delete("/api/support-doc/clear")
async def clear_support_documents(session_id: str):
    session = get_session(session_id)
    session["support_docs_text"] = ""
    session["support_docs_files"] = []
    return {"success": True, "message": "Cleared"}


@slidebot_app.get("/api/support-doc/list/{session_id}")
async def list_support_documents(session_id: str):
    session = get_session(session_id)
    return {
        "success": True,
        "files": session.get("support_docs_files", []),
        "total_text_length": len(session.get("support_docs_text", ""))
    }


# ============ Page Material Upload ============

@slidebot_app.post("/api/page-material/upload")
async def upload_page_material(
    session_id: str = Form(...),
    page_index: int = Form(...),
    file: UploadFile = File(...),
    description: str = Form(default="")
):
    session = get_session(session_id)
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
    excel_extensions = ['.xlsx', '.xls', '.csv']
    allowed_extensions = image_extensions + excel_extensions
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        return {"success": False, "message": "Unsupported"}
    
    outline = session.get("outline_json", [])
    if page_index < 0 or page_index >= len(outline):
        return {"success": False, "message": "Invalid page index"}
    
    material_filename = f"{session_id}_page{page_index}_{int(time.time())}_{file.filename}"
    material_path = MATERIALS_DIR / material_filename
    
    with open(material_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"Material saved: {material_path}")
    
    if file_ext in image_extensions:
        material_type = "image"
        table_text = None
    else:
        material_type = "table"
        table_text = extract_table_from_file(str(material_path), file.filename)
    
    if "page_materials" not in session:
        session["page_materials"] = {}
    
    page_key = str(page_index)
    if page_key not in session["page_materials"]:
        session["page_materials"][page_key] = []
    
    material_data = {
        "filename": file.filename,
        "path": str(material_path),
        "type": material_type,
        "description": description.strip()
    }
    if table_text:
        material_data["table_text"] = table_text
    
    session["page_materials"][page_key].append(material_data)
    add_message(session_id, "assistant", f"Material added to page {page_index + 1}")
    
    return {"success": True, "message": "Success", "page_index": page_index}


@slidebot_app.post("/api/page-material/add-table-text")
async def add_table_text_material(
    session_id: str = Form(...),
    page_index: int = Form(...),
    table_text: str = Form(...),
    description: str = Form(default="")
):
    session = get_session(session_id)
    outline = session.get("outline_json", [])
    if page_index < 0 or page_index >= len(outline):
        return {"success": False, "message": "Invalid page"}
    
    if not table_text.strip():
        return {"success": False, "message": "Empty"}
    
    if "page_materials" not in session:
        session["page_materials"] = {}
    
    page_key = str(page_index)
    if page_key not in session["page_materials"]:
        session["page_materials"][page_key] = []
    
    table_id = f"table_{int(time.time())}"
    
    session["page_materials"][page_key].append({
        "filename": table_id,
        "path": None,
        "type": "table_text",
        "table_text": table_text.strip(),
        "description": description.strip()
    })
    
    add_message(session_id, "assistant", f"Table added to {page_index + 1}")
    return {"success": True, "message": "Success"}


@slidebot_app.delete("/api/page-material/remove")
async def remove_page_material(
    session_id: str,
    page_index: int,
    material_index: int
):
    session = get_session(session_id)
    page_key = str(page_index)
    materials = session.get("page_materials", {}).get(page_key, [])
    
    if material_index < 0 or material_index >= len(materials):
        return {"success": False, "message": "Invalid"}
    
    removed = materials.pop(material_index)
    if removed.get("path"):
        try:
            os.remove(removed["path"])
        except:
            pass
    return {"success": True, "message": "Removed"}


@slidebot_app.get("/api/page-material/list/{session_id}")
async def list_page_materials(session_id: str):
    session = get_session(session_id)
    return {"success": True, "materials": session.get("page_materials", {})}


@slidebot_app.get("/api/page-material/list/{session_id}/{page_index}")
async def list_page_materials_by_page(session_id: str, page_index: int):
    session = get_session(session_id)
    page_key = str(page_index)
    materials = session.get("page_materials", {}).get(page_key, [])
    return {"success": True, "page_index": page_index, "materials": materials}


# ============ Step 1: User Input Ideas ============

@slidebot_app.post("/api/input")
async def submit_user_input(request: UserInputRequest):
    session = get_session(request.session_id)
    session["user_input"] = request.content
    session["stage"] = SessionStage.OUTLINE
    add_message(request.session_id, "user", request.content)
    return {"success": True, "message": "Received", "next_step": "generate_outline"}


# ============ Step 2: Generate Outline ============

@slidebot_app.post("/api/outline/generate")
async def generate_outline(request: UserInputRequest):
    session = get_session(request.session_id)

    if request.page_count:
        session["page_count"] = request.page_count
    if request.page_instructions:
        session["page_instructions"] = request.page_instructions
    if request.design_principles:
        session["design_principles"] = request.design_principles
    if request.template_settings:
        session["template_settings"] = request.template_settings

    page_constraint = f"Strict {request.page_count} pages." if request.page_count else ""
    page_instructions = f"Page instructions: {request.page_instructions}" if request.page_instructions else ""

    audio_transcript = session.get("audio_transcript", "")
    support_docs_text = session.get("support_docs_text", "")
    combined_input = f"{request.content}\\n{audio_transcript}\\n{support_docs_text}"

    prompt = OUTLINE_PROMPT_TEMPLATE.format(user_input=combined_input, page_constraint=page_constraint, page_instructions=page_instructions)
    response_text, retry_info = await generate_text(prompt)

    if not response_text:
        return {"success": False, "message": "Failed"}

    json_data = parse_json_from_text(response_text)

    if json_data and "pages" in json_data:
        session["outline_text"] = response_text
        session["outline_json"] = json_data["pages"]
        session["user_input"] = request.content
        session["stage"] = SessionStage.OUTLINE_REFINE

        add_message(request.session_id, "assistant", f"Outline generated.")
        return {"success": True, "outline_text": response_text, "outline_json": json_data["pages"], "message": "Success"}
    else:
        return {"success": False, "message": "Failed"}


# ============ Step 3: Outline Refine Iteration ============

@slidebot_app.post("/api/outline/refine")
async def refine_outline(request: RefineRequest):
    session = get_session(request.session_id)
    add_message(request.session_id, "user", request.feedback)

    if any(keyword in request.feedback.lower() for keyword in ["ok", "confirm", "yes"]):
        session["stage"] = SessionStage.STYLE
        add_message(request.session_id, "assistant", "Confirmed")
        return {"success": True, "confirmed": True, "message": "Confirmed", "next_step": "generate_style"}

    prompt = REFINE_OUTLINE_PROMPT.format(current_outline=session["outline_text"], user_feedback=request.feedback)
    response_text, retry_info = await generate_text(prompt)

    json_data = parse_json_from_text(response_text)

    if json_data and "pages" in json_data:
        session["outline_text"] = response_text
        session["outline_json"] = json_data["pages"]
        add_message(request.session_id, "assistant", "Refined.")
        return {"success": True, "confirmed": False, "outline_text": response_text, "outline_json": json_data["pages"], "message": "Success"}
    else:
        return {"success": False, "message": "Failed"}


@slidebot_app.post("/api/outline/confirm")
async def confirm_outline(request: BaseRequest):
    session = get_session(request.session_id)
    session["stage"] = SessionStage.STYLE
    add_message(request.session_id, "assistant", "Confirmed")
    return {"success": True, "confirmed": True, "message": "Confirmed", "next_step": "generate_style"}


@slidebot_app.post("/api/outline/update")
async def update_outline(request: OutlineUpdateRequest):
    session = get_session(request.session_id)
    session["outline_json"] = request.outline_json
    outline_text = "\\n\\n".join([f"Page {i+1}\\n{page.get('content', '')}" for i, page in enumerate(request.outline_json)])
    session["outline_text"] = outline_text
    return {"success": True, "message": "Updated"}


# ============ Step 4: Generate Design Style and Drawing Prompt ============

@slidebot_app.post("/api/style/generate")
async def generate_style(request: UserInputRequest):
    session = get_session(request.session_id)

    outline_text = "\\n\\n".join([f"Page {p['page']}: {p.get('theme', p.get('title', ''))}\\n{p.get('content', '')}" for p in session["outline_json"]])

    design_principles = session.get("design_principles", DEFAULT_DESIGN_PRINCIPLES)
    template_settings = session.get("template_settings", {})
    color_scheme = template_settings.get("color_scheme", {})
    font_scheme = template_settings.get("font_scheme", {})
    
    page_number_instruction = "Bottom center page numbers."

    color_scheme_spec = build_color_scheme_spec(color_scheme)
    font_scheme_spec = build_font_scheme_spec(font_scheme)

    prompt = STYLE_GENERATION_PROMPT.format(
        outline=outline_text, design_principles=design_principles,
        color_scheme_spec=color_scheme_spec, font_scheme_spec=font_scheme_spec,
        page_number_instruction=page_number_instruction,
        example_primary='#1C2662', example_secondary='#DAA050',
        example_accent='#BC2424', example_gray='#666464'
    )

    response_text, retry_info = await generate_text(prompt)
    json_data = parse_json_from_text(response_text)

    if json_data and "pages" in json_data:
        session["style_text"] = response_text
        session["style_json"] = json_data["pages"]
        session["stage"] = SessionStage.STYLE_REFINE

        add_message(request.session_id, "assistant", "Style generated")
        style_json_without_prompt = [{"page": p["page"], "theme": p.get("theme", ""), "design_concept": p.get("design_concept", "")} for p in json_data["pages"]]
        return {"success": True, "style_text": response_text, "style_json": style_json_without_prompt, "message": "Success"}
    else:
        return {"success": False, "message": "Failed"}


# ============ Step 5: Design Style Refine Iteration ============

@slidebot_app.post("/api/style/refine")
async def refine_style(request: RefineRequest):
    session = get_session(request.session_id)
    add_message(request.session_id, "user", request.feedback)

    if any(keyword in request.feedback.lower() for keyword in ["generate", "ok", "yes"]):
        session["stage"] = SessionStage.GENERATE
        add_message(request.session_id, "assistant", "Confirmed")
        return {"success": True, "confirmed": True, "message": "Confirmed", "next_step": "generate_images"}

    prompt = REFINE_STYLE_PROMPT.format(current_style=session["style_text"], user_feedback=request.feedback)
    response_text, retry_info = await generate_text(prompt)
    json_data = parse_json_from_text(response_text)

    if json_data and "pages" in json_data:
        session["style_text"] = response_text
        session["style_json"] = json_data["pages"]
        add_message(request.session_id, "assistant", "Refined")
        style_json_without_prompt = [{"page": p["page"], "theme": p.get("theme", ""), "design_concept": p.get("design_concept", "")} for p in json_data["pages"]]
        return {"success": True, "confirmed": False, "style_json": style_json_without_prompt, "message": "Success"}
    else:
        return {"success": False, "message": "Failed"}


@slidebot_app.post("/api/style/confirm")
async def confirm_style(request: BaseRequest):
    session = get_session(request.session_id)
    session["stage"] = SessionStage.GENERATE
    add_message(request.session_id, "assistant", "Confirmed")
    return {"success": True, "confirmed": True, "message": "Confirmed", "next_step": "generate_images"}


# ============ Step 6: Upload Reference Image ============

SUPPORTED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}

@slidebot_app.post("/api/reference/upload")
async def upload_reference_image(session_id: str, file: UploadFile = File(...), type: str = "reference"):
    session = get_session(session_id)
    original_ext = Path(file.filename).suffix.lower() or '.png'
    file_path = REFERENCE_DIR / f"{session_id}_reference{original_ext}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    session["reference_image_path"] = str(file_path)
    session["reference_type"] = type

    template_analysis = None
    if type == "template":
        template_analysis = analyze_template_design(str(file_path))
        if template_analysis:
            session["template_analysis"] = template_analysis

    return {"success": True, "message": "Success", "file_path": str(file_path), "type": type}


@slidebot_app.post("/api/logo/upload")
async def upload_logo(session_id: str, file: UploadFile = File(...)):
    session = get_session(session_id)
    original_ext = Path(file.filename).suffix.lower()
    logo_path = REFERENCE_DIR / f"{session_id}_logo{original_ext}"
    with open(logo_path, "wb") as f:
        content = await file.read()
        f.write(content)
    session["custom_logo_path"] = str(logo_path)
    return {"success": True, "message": "Success"}


# ============ Single Page Refine and Regenerate ============

@slidebot_app.post("/api/page/refine-and-regenerate")
async def refine_page_and_regenerate(request: RefinePageRequest):
    session = get_session(request.session_id)
    style_pages = session.get("style_json", [])
    current_page = style_pages[request.page_index]
    page_num = request.page_index + 1
    
    current_image_path = None
    generated_images = session.get("generated_images", [])
    if request.page_index < len(generated_images) and generated_images[request.page_index]:
        current_image_path = generated_images[request.page_index].get("image_path")

    prompt = REFINE_PAGE_PROMPT.format(
        page_num=page_num, theme=current_page.get("theme", ""),
        design_concept=current_page.get("design_concept", ""),
        current_prompt=current_page.get("prompt", ""), user_feedback=request.feedback
    )
    response_text, text_retry_info = await generate_text(prompt)
    json_data = parse_json_from_text(response_text)

    if json_data:
        updated_page = {
            "page": page_num,
            "theme": json_data.get("theme", current_page.get("theme", "")),
            "design_concept": json_data.get("design_concept", ""),
            "prompt": json_data.get("prompt", "")
        }
        session["style_json"][request.page_index] = updated_page

        refine_prompt = updated_page["prompt"]
        if current_image_path:
            refine_prompt = f"REFINE MODE: {request.feedback}\\n\\n{refine_prompt}"

        output_path = OUTPUT_DIR / f"{request.session_id}_page{page_num}.jpg"
        success, image_retry_info = await generate_ppt_image(
            prompt=refine_prompt, output_path=output_path,
            reference_image_path=current_image_path if current_image_path else session.get("reference_image_path"),
            custom_logo_path=session.get("custom_logo_path"),
            reference_type="refine" if current_image_path else session.get("reference_type", "reference"),
            template_analysis=session.get("template_analysis")
        )

        if success:
            full_filename = f"{request.session_id}_page{page_num}.jpg"
            image_info = {"page": page_num, "theme": updated_page.get("theme", ""), "image_path": str(output_path), "filename": full_filename}

            while len(session["generated_images"]) <= request.page_index:
                session["generated_images"].append(None)
            session["generated_images"][request.page_index] = image_info

            add_message(request.session_id, "assistant", f"Refined page {page_num}")
            return {"success": True, "image_path": str(output_path), "message": "Success"}
        else:
            return {"success": False, "message": "Failed"}
    else:
        return {"success": False, "message": "Failed"}


# ============ Step 7: Generate PPT Image Page by Page ============

@slidebot_app.post("/api/image/generate")
async def generate_single_image(request: GenerateImageRequest):
    session = get_session(request.session_id)
    style_pages = session.get("style_json", [])
    page_style = style_pages[request.page_index]
    prompt = page_style.get("prompt", "")

    output_path = OUTPUT_DIR / f"{request.session_id}_page{request.page_index + 1}.jpg"
    page_materials = session.get("page_materials", {}).get(str(request.page_index), [])

    success, retry_info = await generate_ppt_image(
        prompt=prompt, output_path=output_path,
        reference_image_path=session.get("reference_image_path"),
        custom_logo_path=session.get("custom_logo_path"),
        reference_type=session.get("reference_type", "reference"),
        template_analysis=session.get("template_analysis"),
        page_materials=page_materials
    )

    if success:
        full_filename = f"{request.session_id}_page{request.page_index + 1}.jpg"
        image_info = {"page": request.page_index + 1, "theme": page_style.get("theme", ""), "image_path": str(output_path), "filename": full_filename}
        while len(session["generated_images"]) <= request.page_index:
            session["generated_images"].append(None)
        session["generated_images"][request.page_index] = image_info
        add_message(request.session_id, "assistant", f"Generated page {request.page_index + 1}")
        return {"success": True, "image_path": str(output_path), "filename": full_filename}
    else:
        raise HTTPException(status_code=500, detail="Failed")


@slidebot_app.post("/api/image/generate-all")
async def generate_all_images(request: GenerateAllImagesRequest):
    session = get_session(request.session_id)
    style_pages = session.get("style_json", [])
    session["stage"] = SessionStage.GENERATE
    results = []

    for i, page_style in enumerate(style_pages):
        prompt = page_style.get("prompt", "")
        if not prompt: continue
        output_path = OUTPUT_DIR / f"{request.session_id}_page{i + 1}.jpg"
        page_materials = session.get("page_materials", {}).get(str(i), [])

        success, retry_info = await generate_ppt_image(
            prompt=prompt, output_path=output_path,
            reference_image_path=session.get("reference_image_path"),
            custom_logo_path=session.get("custom_logo_path"),
            reference_type=session.get("reference_type", "reference"),
            template_analysis=session.get("template_analysis"),
            page_materials=page_materials
        )

        result = {
            "page": i + 1, "theme": page_style.get("theme", ""), "success": success,
            "image_path": str(output_path) if success else None,
            "filename": f"page{i + 1}.jpg" if success else None
        }
        results.append(result)

        if success:
            while len(session["generated_images"]) <= i:
                session["generated_images"].append(None)
            session["generated_images"][i] = result

    session["stage"] = SessionStage.COMPLETE
    add_message(request.session_id, "assistant", "All generated")
    return {"success": True, "results": results}


# ============ Step 8: Download Package ============

@slidebot_app.get("/api/download/{session_id}")
async def download_ppt_package(session_id: str):
    session = get_session(session_id)
    images = session.get("generated_images", [])
    zip_path = OUTPUT_DIR / f"{session_id}_PPT.zip"

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for img in images:
            if img and img.get("image_path") and os.path.exists(img["image_path"]):
                zipf.write(img["image_path"], img["filename"])

    return FileResponse(zip_path, media_type="application/zip", filename=f"PPT.zip")


@slidebot_app.get("/api/download/{session_id}/pdf")
async def download_ppt_pdf(session_id: str):
    session = get_session(session_id)
    images = session.get("generated_images", [])
    valid_images = []
    for img in images:
        if img and img.get("image_path") and os.path.exists(img["image_path"]):
            try:
                pil_img = Image.open(img["image_path"])
                if pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')
                valid_images.append(pil_img)
            except Exception as e:
                logger.error(f"Err {e}")

    pdf_path = OUTPUT_DIR / f"{session_id}_PPT.pdf"
    if len(valid_images) > 1:
        valid_images[0].save(pdf_path, "PDF", save_all=True, append_images=valid_images[1:], resolution=150.0)
    elif len(valid_images) == 1:
        valid_images[0].save(pdf_path, "PDF", resolution=150.0)

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"PPT.pdf")


@slidebot_app.get("/api/image/{filename}")
async def get_image(filename: str):
    exact_path = OUTPUT_DIR / filename
    if exact_path.exists():
        return FileResponse(exact_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Not found")


# ============ Chat Interface ============

@slidebot_app.post("/api/chat")
async def chat(request: UserInputRequest):
    session = get_session(request.session_id)
    stage = session["stage"]
    add_message(request.session_id, "user", request.content)

    if stage == SessionStage.INPUT:
        return await generate_outline(request)
    elif stage in [SessionStage.OUTLINE, SessionStage.OUTLINE_REFINE]:
        return await refine_outline(RefineRequest(session_id=request.session_id, feedback=request.content))
    elif stage in [SessionStage.STYLE, SessionStage.STYLE_REFINE]:
        return await refine_style(RefineRequest(session_id=request.session_id, feedback=request.content))
    elif stage == SessionStage.GENERATE:
        return {"success": True, "message": "Generating"}
    elif stage == SessionStage.COMPLETE:
        return {"success": True, "message": "Done"}

    return {"success": False, "message": "Unknown"}


@slidebot_app.get("/api/visit/count")
async def get_visit():
    return {"count": await get_visit_count()}


@slidebot_app.post("/api/visit/increment")
async def increment_visit():
    return {"count": await increment_visit_count()}


# ============ Static File Service ============
def setup_static_files():
    if FRONTEND_BUILD_DIR.exists():
        static_dir = FRONTEND_BUILD_DIR / "static"
        if static_dir.exists():
            slidebot_app.mount("/static", StaticFiles(directory=static_dir), name="static")

        @slidebot_app.get("/{full_path:path}")
        async def serve_frontend(full_path: str):
            file_path = FRONTEND_BUILD_DIR / full_path
            if file_path.exists() and file_path.is_file():
                return FileResponse(file_path)
            return FileResponse(FRONTEND_BUILD_DIR / "index.html")
    else:
        logger.warning(f"Frontend build directory does not exist: {FRONTEND_BUILD_DIR} (API only)")

setup_static_files()

