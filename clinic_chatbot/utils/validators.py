"""
Validation Utilities - Responsibilities:
- Provide ALL validation functions used across the application
- Handle data format validation and normalization  
- Provide consistent error messaging
- Support for different locale-specific validation rules
- Keep all validation logic centralized and reusable
- Include composite validation for complex objects
"""

import re
from typing import Tuple, Optional, List, Dict, Any
from datetime import datetime, timedelta

def is_valid_chinese_name(name: str) -> bool:
    """Validate if the name is a valid Chinese name or common English name."""
    if not name or len(name) < 2 or len(name) > 10:
        return False
    
    # Check for Chinese characters or common English names
    chinese_pattern = r'^[\u4e00-\u9fa5]+$'
    english_pattern = r'^[a-zA-Z\s]+$'
    
    return bool(re.match(chinese_pattern, name) or re.match(english_pattern, name))

import re
from typing import Tuple

def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """验证香港电话号码格式
    Hong Kong Phone Number Format
    Length: 8 digits
    Mobile numbers: Start with 4, 5, 6, 7, 8, or 9
    Landline numbers: Start with 2 or 3
    Country code: +852 (optional in local format)
    """
    if not phone:
        return False, "Phone number cannot be empty"
    
    # Remove spaces, dashes, and country code if present
    clean_phone = re.sub(r'[\s\-]', '', phone)
    clean_phone = re.sub(r'^(\+852|852)', '', clean_phone)

    # Match 8-digit Hong Kong numbers starting with valid prefixes
    if re.match(r'^[2-9]\d{7}$', clean_phone):
        return True, clean_phone
    else:
        return False, "Please provide a valid Hong Kong phone number."


def validate_policy_number(policy: str) -> Tuple[bool, str]:
    """Validate policy number format"""
    if not policy:
        return False, "Policy number cannot be empty"
    
    # Basic validation - alphanumeric, 6-20 characters
    if re.match(r'^[A-Za-z0-9]{6,20}$', policy):
        return True, policy.upper()
    else:
        return False, "Policy number format is incorrect, please check and re-enter"

def validate_appointment_type(apt_type: str, valid_types: Optional[List[str]] = None) -> Tuple[bool, str]:
    """Validate appointment type"""
    if not apt_type:
        return False, "Appointment type cannot be empty"
    
    if valid_types is None:
        valid_types = get_clinic_appointment_types()
    
    # Fuzzy matching for common variations
    apt_type_lower = apt_type.lower()
    for valid_type in valid_types:
        if valid_type in apt_type or apt_type in valid_type:
            return True, valid_type
    
    # If no exact match, accept the input but flag for review
    return True, apt_type

def normalize_date_expression(date_expr: str) -> Optional[str]:
    """Normalize date expression"""
    if not date_expr:
        return None
    
    date_expr = date_expr.lower().strip()
    today = datetime.now()
    
    # Handle relative dates
    if "今天" in date_expr or "今日" in date_expr:
        return today.strftime("%Y-%m-%d")
    elif "明天" in date_expr or "明日" in date_expr:
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d")
    elif "后天" in date_expr:
        day_after = today + timedelta(days=2)
        return day_after.strftime("%Y-%m-%d")
    elif "下周" in date_expr:
        next_week = today + timedelta(days=7)
        return next_week.strftime("%Y-%m-%d")
    
    # Handle specific date patterns
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # 2024-01-15
        r'(\d{1,2})月(\d{1,2})日',        # 1月15日
        r'(\d{1,2})/(\d{1,2})',          # 1/15
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_expr)
        if match:
            try:
                if len(match.groups()) == 3:  # Full date
                    year, month, day = match.groups()
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                elif len(match.groups()) == 2:  # Month and day only
                    month, day = match.groups()
                    return f"{today.year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue
    
    # If no pattern matches, return original
    return date_expr

def normalize_time_slot(time_slot: str) -> Optional[str]:
    """Normalize time slot expression"""
    if not time_slot:
        return None
    
    time_slot = time_slot.lower().strip()
    
    # Map common time expressions
    time_mappings = {
        "早上": "上午",
        "早晨": "上午", 
        "上午": "上午",
        "中午": "下午",
        "下午": "下午",
        "晚上": "晚上",
        "夜间": "晚上"
    }
    
    for key, value in time_mappings.items():
        if key in time_slot:
            return value
    
    # Handle specific time ranges
    if any(x in time_slot for x in ["9", "10", "11"]):
        return "上午"
    elif any(x in time_slot for x in ["14", "15", "16", "17"]):
        return "下午"
    elif any(x in time_slot for x in ["18", "19", "20"]):
        return "晚上"
    
    return time_slot

def validate_age_range(age: int, min_age: int = 0, max_age: int = 150) -> Tuple[bool, str]:
    """Validate age range"""
    if age < min_age:
        return False, f"Age cannot be less than {min_age} years"
    elif age > max_age:
        return False, f"Age cannot be greater than {max_age} years"
    else:
        return True, ""

def validate_gender(gender: str) -> Tuple[bool, str]:
    """Validate gender"""
    if not gender:
        return True, ""  # Gender is optional
    
    valid_genders = ["男", "女", "其他"]
    if gender in valid_genders:
        return True, gender
    
    # Try to normalize common variations
    if gender.lower() in ["male", "m"]:
        return True, "男"
    elif gender.lower() in ["female", "f"]:
        return True, "女"
    else:
        return False, "Valid options are: 男、女、其他"

# Composite validation functions (moved from EntityValidator)
def validate_patient_info(patient_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate patient information - composite validation function"""
    errors = []
    
    # Validate name
    name = patient_info.get("name")
    if name and not is_valid_chinese_name(name):
        errors.append("Name format is incorrect")
    
    # Validate age
    age = patient_info.get("age")
    if age is not None:
        try:
            age_int = int(age)
            is_valid, error_msg = validate_age_range(age_int)
            if not is_valid:
                errors.append(error_msg)
        except ValueError:
            errors.append("Age must be a number")

    # Validate gender
    gender = patient_info.get("gender")
    if gender:
        is_valid, normalized_gender = validate_gender(gender)
        if not is_valid:
            errors.append(normalized_gender)  # Error message
        else:
            patient_info["gender"] = normalized_gender  # Update with normalized value

    return len(errors) == 0, errors

def validate_preferred_time(time_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate preferred time information - composite validation function"""
    errors = []
    
    date_expr = time_info.get("date")
    if date_expr:
        normalized_date = normalize_date_expression(date_expr)
        if normalized_date:
            time_info["date"] = normalized_date  # Update with normalized value
        else:
            errors.append("Date format cannot be recognized, please provide a specific date")

    # Normalize time slot if present
    time_slot = time_info.get("time_slot")
    if time_slot:
        normalized_slot = normalize_time_slot(time_slot)
        if normalized_slot:
            time_info["time_slot"] = normalized_slot

    return len(errors) == 0, errors

def get_clinic_appointment_types() -> List[str]:
    """Get supported clinic appointment types"""
    return [
            "普通科", "内科", "外科", "儿科", "妇产科", "眼科", "耳鼻喉科", "口腔科", "皮肤科",
            "骨科", "泌尿科", "心血管科", "呼吸科", "消化科", "内分泌科", "肿瘤科",
            "精神科", "康复科", "中医科", "疼痛科", "麻醉科", "营养科", "检验科", "影像科"
        ]
