import os
from typing import Dict, Any
from dotenv import load_dotenv


# Gemini Configuration
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
GEMINI_MODEL = "gemini-2.0-flash"

# Conversation Configuration
MAX_CONVERSATION_TURNS = 20
CONVERSATION_TIMEOUT = 1800  # 30 minutes

LANGUAGE = "zh-TC" # Options: "en", "zh-TC"

# Mandatory Fields Configuration
MANDATORY_FIELDS = {
    "预约类型": {
        "type": "string",
        "description": "预约类型 (如：体检、专科咨询、复诊等)",
        "required": True
    },
    "病人信息": {
        "type": "object",
        "description": "病人基本信息",
        "required": True,
        "fields": {
            "姓名": {"type": "string", "required": True},
            "年龄": {"type": "integer", "required": False},
            "性别": {"type": "string", "required": False}
        }
    },
    "保单号码": {
        "type": "string", 
        "description": "保险保单号码",
        "required": True
    },
    "可预约时间": {
        "type": "object",
        "description": "期望的预约时间",
        "required": True,
        "fields": {
            "日期": {"type": "string", "required": True},
            "时间段": {"type": "string", "required": False}
        }
    },
    "电话号码": {
        "type": "string",
        "description": "联系电话号码", 
        "required": True
    }
}

# Mock doctor data for testing
MOCK_DOCTORS = [
    {"id": "dr_wang", "name": "王医生", "specialty": "内科"},
    {"id": "dr_li", "name": "李医生", "specialty": "外科"},
    {"id": "dr_zhang", "name": "张医生", "specialty": "儿科"}
]