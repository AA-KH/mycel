

import os
from pathlib import Path


from dotenv import load_dotenv
load_dotenv()



# Gemini API Configuration
GEMINI_API_BASE = os.environ.get("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta/models")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") 

# iFLYTEK ASR Configuration (Optional: for voice transcription)
XFYUN_APPID = os.environ.get("IFLYTEK_APP_ID", "")
XFYUN_SECRET_KEY = os.environ.get("IFLYTEK_API_SECRET", "")
LFASR_HOST = 'https://raasr.xfyun.cn/v2/api'


INVITE_CODES_FILE = Path("./invite_codes.json")


RECORDS_DIR = Path("./records")
RECORDS_DIR.mkdir(exist_ok=True)


LOGIN_RECORDS_FILE = RECORDS_DIR / "login_records.csv"


OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


REFERENCE_DIR = Path("./references")
REFERENCE_DIR.mkdir(exist_ok=True)


AUDIO_DIR = Path("./audio")
AUDIO_DIR.mkdir(exist_ok=True)


MATERIALS_DIR = Path("./materials")
MATERIALS_DIR.mkdir(exist_ok=True)


SUPPORT_DOCS_DIR = Path("./support_docs")
SUPPORT_DOCS_DIR.mkdir(exist_ok=True)


FRONTEND_BUILD_DIR = Path("./frontend/build")


VISIT_COUNT_FILE = RECORDS_DIR / "visit_count.txt"



COLORS = {
    "blue": "#1C2662",      
    "gold": "#DAA050",      
    "red": "#BC2424",       
    "gray": "#666464",     
    "light_gray": "#F5F5F5",
    "white": "#FFFFFF",
}


MAX_RETRIES = 3
RETRY_DELAY = 5  
