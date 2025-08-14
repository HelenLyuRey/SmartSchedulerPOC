"""
Entity Extractor - Responsibilities:
- Coordinate entity extraction process using LLM service
- Merge new entities with existing ones intelligently
- Use utils.validators directly for all validation
- Handle entity conflicts and corrections
- Provide smart entity completion logic
- Track extraction confidence and quality
"""

from typing import Dict, Any, List, Optional, Tuple
from models import BookingEntities, PatientInfo, PreferredTime, ConversationManager
from .llm_service import LLMService
from utils.validators import (
    validate_phone_number, 
    validate_policy_number, 
    validate_appointment_type,
    validate_patient_info,
    validate_preferred_time,
    get_clinic_appointment_types
)

class SmartEntityMerger:
    """
    Smart Entity Merger - Responsibilities:
    - Intelligently merge new entities with existing ones
    - Use utils.validators directly for validation during merging
    - Handle entity updates and corrections
    - Maintain entity history for rollback
    - Detect and resolve entity conflicts
    """
    
    def merge_entities(self, current_entities: BookingEntities, new_entities: Dict[str, Any]) -> Tuple[BookingEntities, List[str]]:
        """
        Merge new entities with current ones, applying direct utils validators.
        Returns: (merged_entities, validation_errors)
        """
        merged = current_entities.copy(deep=True)
        all_errors = []
        
        for key, value in new_entities.items():
            if not value:  # Skip None/empty values
                continue
                
            if key == "booking_type":
                # Direct call to utils validator
                is_valid, result = validate_appointment_type(value, get_clinic_appointment_types())
                if is_valid:
                    merged.booking_type = result
                else:
                    all_errors.append(f"booking_type: {result}")
                    
            elif key == "phone_number":
                # Direct call to utils validator
                is_valid, result = validate_phone_number(str(value))
                if is_valid:
                    merged.phone_number = result
                else:
                    all_errors.append(f"phone_number: {result}")
                    
            elif key == "policy_number":
                # Direct call to utils validator
                is_valid, result = validate_policy_number(str(value))
                if is_valid:
                    merged.policy_number = result
                else:
                    all_errors.append(f"policy_number: {result}")
                    
            elif key == "patient_info" and isinstance(value, dict):
                if not merged.patient_info:
                    merged.patient_info = PatientInfo()
                
                # Direct call to utils composite validator
                patient_copy = value.copy()
                is_valid, errors = validate_patient_info(patient_copy)
                if not is_valid:
                    all_errors.extend([f"patient_info: {error}" for error in errors])
                else:
                    # Update with validated/normalized values
                    for patient_key, patient_value in patient_copy.items():
                        if patient_value:
                            setattr(merged.patient_info, patient_key, patient_value)
                        
            elif key == "available_time" and isinstance(value, dict):
                if not merged.available_time:
                    merged.available_time = PreferredTime()
                
                # Direct call to utils composite validator
                time_copy = value.copy()
                is_valid, errors = validate_preferred_time(time_copy)
                if not is_valid:
                    all_errors.extend([f"available_time: {error}" for error in errors])
                else:
                    # Update with validated/normalized values
                    for time_key, time_value in time_copy.items():
                        if time_value:
                            setattr(merged.available_time, time_key, time_value)
        
        return merged, all_errors

class EntityExtractor:
    """
    Main Entity Extractor - Responsibilities:
    - Orchestrate the complete entity extraction process
    - Coordinate between LLM service and entity merging
    - Track extraction quality and confidence
    - Handle extraction errors gracefully
    - Provide detailed extraction reports
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.merger = SmartEntityMerger()
        self.extraction_history: List[Dict[str, Any]] = []
    
    def extract_and_merge(self, conversation: ConversationManager, user_message: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Extract entities from user message and merge with current conversation entities.
        Returns: (success, extraction_info)
        """
        extraction_info = {
            "message": user_message,
            "extracted_entities": {},
            "merged_successfully": False,
            "validation_errors": [],
            "entities_before": conversation.entities.to_dict(),
            "entities_after": None
        }
        
        try:
            # Get current entities as dict for LLM
            current_entities_dict = conversation.entities.to_dict()
            conversation_context = conversation.get_conversation_context()
            
            # Extract entities using LLM
            extracted = self.llm_service.extract_entities(
                user_message, 
                current_entities_dict, 
                conversation_context
            )
            
            extraction_info["extracted_entities"] = extracted
            
            if not extracted:
                return False, extraction_info
            
            # Merge with existing entities (now with direct utils validation)
            original_entities = conversation.entities
            merged_entities, validation_errors = self.merger.merge_entities(original_entities, extracted)
            
            # Update conversation entities
            conversation.entities = merged_entities
            extraction_info["entities_after"] = merged_entities.to_dict()
            extraction_info["validation_errors"] = validation_errors
            extraction_info["merged_successfully"] = True
            
            # Store extraction history
            self.extraction_history.append(extraction_info.copy())
            
            return True, extraction_info
            
        except Exception as e:
            extraction_info["error"] = str(e)
            print(f"Entity extraction error: {e}")
            return False, extraction_info
    
    def get_missing_fields_question(self, conversation: ConversationManager) -> str:
        """Generate a question asking about missing fields"""
        missing_fields = conversation.entities.get_missing_fields()
        if not missing_fields:
            return ""
        
        conversation_context = conversation.get_conversation_context()
        current_entities = conversation.entities.to_dict()
        
        return self.llm_service.generate_missing_fields_question(
            missing_fields, 
            conversation_context, 
            current_entities
        )
    
    def get_extraction_quality_score(self) -> float:
        """Calculate the quality score of entity extraction"""
        if not self.extraction_history:
            return 0.0
        
        successful_extractions = sum(1 for h in self.extraction_history if h["merged_successfully"])
        return successful_extractions / len(self.extraction_history)
    
    def get_extraction_summary(self) -> Dict[str, Any]:
        """Get extraction summary statistics"""
        if not self.extraction_history:
            return {"total_extractions": 0, "success_rate": 0.0}
        
        total = len(self.extraction_history)
        successful = sum(1 for h in self.extraction_history if h["merged_successfully"])
        
        return {
            "total_extractions": total,
            "successful_extractions": successful,
            "success_rate": successful / total if total > 0 else 0.0,
            "recent_extractions": self.extraction_history[-5:]  # Last 5 extractions
        }