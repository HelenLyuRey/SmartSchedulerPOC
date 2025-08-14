from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import re

class PatientInfo(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    
    @validator('age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v
    
    @validator('gender')
    def validate_gender(cls, v):
        if v is not None and v not in ['男', '女', '其他']:
            return None  # Let LLM handle normalization
        return v

class PreferredTime(BaseModel):
    date: Optional[str] = None
    time_slot: Optional[str] = None

class BookingEntities(BaseModel):
    booking_type: Optional[str] = None
    patient_info: Optional[PatientInfo] = PatientInfo()
    policy_number: Optional[str] = None
    available_time: Optional[PreferredTime] = PreferredTime()
    phone_number: Optional[str] = None
    
    def get_missing_fields(self) -> List[str]:
        """Return missing mandatory fields"""
        missing = []
        
        if not self.booking_type:
            missing.append("預約類型")
            
        if not self.patient_info or not self.patient_info.name:
            missing.append("病人資訊")
            
        if not self.policy_number:
            missing.append("保單號碼")

        if not self.available_time or not self.available_time.date:
            missing.append("可預約時間")

        if not self.phone_number:
            missing.append("電話號碼")

        return missing
    
    def is_complete(self) -> bool:
        """Check if all mandatory fields are filled"""
        return len(self.get_missing_fields()) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            "booking_type": self.booking_type,
            "patient_info": {
                "name": self.patient_info.name if self.patient_info else None,
                "age": self.patient_info.age if self.patient_info else None,
                "gender": self.patient_info.gender if self.patient_info else None,
            },
            "policy_number": self.policy_number,
            "available_time": {
                "date": self.available_time.date if self.available_time else None,
                "time_slot": self.available_time.time_slot if self.available_time else None,
            },
            "phone_number": self.phone_number
        }

class DoctorSlot(BaseModel):
    doctor_id: str
    doctor_name: str
    specialty: str
    date: str
    start_time: str
    end_time: str
    available: bool = True

class BookingConfirmation(BaseModel):
    booking_id: str
    patient_name: str
    doctor_name: str
    appointment_type: str
    date: str
    time: str
    phone: str
    policy_number: str
    created_at: datetime = Field(default_factory=datetime.now)