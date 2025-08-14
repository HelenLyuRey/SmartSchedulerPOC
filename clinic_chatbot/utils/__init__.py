"""
Utilities Package - Responsibilities:
- Provide ALL utility functions used across the application
- Handle data validation, normalization, and formatting
- Support cross-cutting concerns like logging and error handling
- Centralized validation logic for consistency
- Include composite validation functions
"""

from .validators import (
    is_valid_chinese_name, 
    validate_phone_number, 
    validate_policy_number,
    validate_appointment_type,
    normalize_date_expression,
    normalize_time_slot, 
    validate_age_range,
    validate_gender,
    validate_patient_info,
    validate_preferred_time,
    get_clinic_appointment_types
)

__all__ = [
    'is_valid_chinese_name', 
    'validate_phone_number',
    'validate_policy_number', 
    'validate_appointment_type',
    'normalize_date_expression',
    'normalize_time_slot', 
    'validate_age_range',
    'validate_gender',
    'validate_patient_info',
    'validate_preferred_time',
    'get_clinic_appointment_types'
]