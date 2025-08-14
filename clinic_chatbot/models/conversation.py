from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from .entities import BookingEntities, DoctorSlot

class ConversationState(Enum):
    GREETING = "greeting"
    EXTRACTING_ENTITIES = "extracting_entities" 
    COLLECTING_MISSING = "collecting_missing"
    SHOWING_AVAILABILITY = "showing_availability"
    CONFIRMING_BOOKING = "confirming_booking"
    COMPLETED = "completed"
    ERROR = "error"

class ConversationManager:
    def __init__(self):
        self.conversation_id = f"conv_{int(datetime.now().timestamp())}"
        self.state = ConversationState.GREETING
        self.entities = BookingEntities()
        self.message_history: List[Dict[str, str]] = []
        self.available_slots: List[DoctorSlot] = []
        self.selected_slot: Optional[DoctorSlot] = None
        self.turn_count = 0
        self.created_at = datetime.now()
        
    def add_message(self, role: str, content: str):
        """Add chat history message"""
        self.message_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        if role == "user":
            self.turn_count += 1
    
    def update_entities(self, new_entities: Dict[str, Any]):
        for key, value in new_entities.items():
            if key == "patient_info" and isinstance(value, dict):  
                if not self.entities.patient_info:
                    from .entities import PatientInfo
                    self.entities.patient_info = PatientInfo()
                
                for patient_key, patient_value in value.items():
                    if patient_value:  # Only update if value is not None/empty
                        setattr(self.entities.patient_info, patient_key, patient_value)
                        
            elif key == "available_time" and isinstance(value, dict):  
                if not self.entities.available_time:
                    from .entities import PreferredTime
                    self.entities.available_time = PreferredTime()
                
                for time_key, time_value in value.items():
                    if time_value:  # Only update if value is not None/empty
                        setattr(self.entities.available_time, time_key, time_value)
            else:
                if value:  # Only update if value is not None/empty
                    setattr(self.entities, key, value)
    
    def get_conversation_context(self) -> str:
        recent_messages = self.message_history[-6:]  # Last 3 exchanges
        context = ""
        for msg in recent_messages:
            context += f"{msg['role']}: {msg['content']}\n"
        return context
    
    def set_available_slots(self, slots: List[DoctorSlot]):
        self.available_slots = slots
        
    def select_slot(self, slot: DoctorSlot):
        self.selected_slot = slot
        
    def get_summary(self) -> Dict[str, Any]:
        """Chat history summary"""
        return {
            "conversation_id": self.conversation_id,
            "state": self.state.value,
            "turn_count": self.turn_count,
            "entities": self.entities.to_dict(),
            "missing_fields": self.entities.get_missing_fields(),
            "is_complete": self.entities.is_complete(),
            "available_slots_count": len(self.available_slots),
            "selected_slot": self.selected_slot.dict() if self.selected_slot else None
        }