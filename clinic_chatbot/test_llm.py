"""
Test script for LLM Service - Responsibilities:
- Test entity extraction functionality
- Test missing fields question generation  
- Verify JSON parsing works correctly
- Test different user input scenarios
"""

from services.llm_service import LLMService
from services.entity_extractor import EntityExtractor, SmartEntityMerger
from models import ConversationManager, BookingEntities
from config import GEMINI_API_KEY

def test_llm_service():
    if GEMINI_API_KEY == "your-api-key-here":
        print("Please set your GEMINI_API_KEY in config.py")
        return
    llm = LLMService()
    
    # Test greeting
    print("=== Testing Greeting ===")
    greeting = llm.generate_greeting()
    print(f"Greeting: {greeting}")
    
    # Test entity extraction
    print("\n=== Testing Entity Extraction ===")
    test_message = "我想预约明天上午体检，我叫张三，30岁，男性，我的保单号是ABC123"
    current_entities = {}
    
    entities = llm.extract_entities(test_message, current_entities)
    print(f"Extracted entities: {entities}")
    
    # Use SmartEntityMerger to determine missing fields
    print("\n=== Testing Missing Fields ===")
    merger = SmartEntityMerger()
    booking_entities = BookingEntities()

    # Merge extracted entities
    merged, validation_errors = merger.merge_entities(booking_entities, entities)
    print(f"Merged entities: {merged.to_dict()}")
    print(f"Validation errors: {validation_errors}")

    # Get missing fields dynamically
    missing_fields = merged.get_missing_fields()
    print(f"Missing fields: {missing_fields}")

    # Generate follow-up question only if there are missing fields
    if missing_fields:
        question = llm.generate_missing_fields_question(missing_fields, "", entities)
        print(f"Follow-up question: {question}")
    else:
        print("No missing fields detected. No follow-up question needed.")


if __name__ == "__main__":
    test_llm_service()