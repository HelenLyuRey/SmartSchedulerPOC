"""
LLM Service - Responsibilities:
- Handle all interactions with Google Gemini API
- Manage prompt templates for different conversation stages
- Parse and structure LLM responses
- Handle API errors and retries
- Provide consistent interface for all LLM operations
"""

import google.generativeai as genai
from typing import Dict, Any, Optional, List
import json
import re
from config import GEMINI_API_KEY, GEMINI_MODEL

class GeminiService:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
        
    def generate_response(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text.strip()
            except Exception as e:
                print(f"LLM API error (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    return None
        return None

class PromptTemplates:
    """
    Prompt Templates - Responsibilities:
    - Store all prompt templates used throughout the conversation
    - Provide dynamic prompt generation based on context
    - Maintain consistent prompt structure and formatting
    """
    
    @staticmethod
    def entity_extraction_prompt(user_message: str, current_entities: Dict[str, Any], conversation_context: str = "") -> str:

        return f"""
        
You are a professional hospital appointment assistant. Please extract appointment-related information from the user's message.

## Currently collected information:
{json.dumps(current_entities, ensure_ascii=False, indent=2)}

## Conversation history:
{conversation_context}

## User's latest message
{user_message}

Please extract the following information and return it in JSON format. If any information is missing, set it to null:
- Appointment Type: e.g., health check-up, specialist consultation, follow-up visit  
- Patient Information: including name, age, gender  
- Policy Number: insurance policy number  
- Available Appointment Time: including date and time preference  
- Phone Number: contact number  

## Output format:
Please output in Traditional Chinese, and ensure the JSON structure is as follows:
{{
"booking_type": "健康檢查",
"patient_info": {{
    "name": "張三",
    "age": 30,
    "gender": "男"
}},
"policy_number": "ABC123",
"available_time": {{
    "date": "明天",
    "time_slot": "上午"
}},
"phone_number": "98772212"
}}

"""


    @staticmethod 
    def missing_fields_prompt(missing_fields: List[str], conversation_context: str, current_entities: Dict[str, Any]) -> str:
        """
        Generate a natural and friendly prompt to ask for missing appointment information.

        Parameters:
        - missing_fields: List of required fields not yet provided by the user.
        - conversation_context: The history of the conversation so far.
        - current_entities: Dictionary of information already collected from the user.

        Returns:
        - A formatted string prompt with instructions for generating a question.
        """
        return f"""
    ## Role Description
    You are a **friendly hospital appointment assistant**. The user has not yet provided the following required information:
    **Missing Fields:** {', '.join(missing_fields)}

    ## Current Collected Information
    {json.dumps(current_entities, ensure_ascii=False, indent=2)}

    ## Conversation History
    {conversation_context}

    ## Prompt Generation Instructions
    Please generate a **natural and friendly question** to ask for the missing information. Follow these guidelines:
    1. Ask for **only 1–2 of the most important missing fields** at a time.
    2. Use **natural and friendly language**—avoid sounding robotic or overly formal.
    3. **Explain why** the information is needed, if possible.
    4. Ensure the question **flows naturally** from the conversation history.

    ## Priority Order for Missing Fields
    1. Appointment Type
    2. Patient Name
    3. Appointment Date
    4. Insurance Policy Number
    5. Phone Number

    ## Output Format
    Return the result in **JSON format** and in Traditional Chinese.
    **Example Output:**
    {{
    "missing_fields_followup": 請問可以提供電話號碼嗎？這樣我可以更好地幫您安排預約。",
    }}
    """


    @staticmethod
    def slot_selection_prompt(user_message: str, available_slots: List[Dict[str, Any]]) -> str:
        """Handle user's time slot selection - English prompt, number output"""
        slots_text = ""
        for i, slot in enumerate(available_slots, 1):
            slots_text += f"{i}. {slot['doctor_name']} - {slot['date']} {slot['start_time']}-{slot['end_time']} ({slot['specialty']})\n"
        
        return f"""
    ## Role Description
    You are analyzing which appointment slot the user wants to select.

    ## Available Time Slots
    {slots_text}

    ## User's Selection Message
    "{user_message}"

    ## Task
    Analyze which time slot the user wants to choose and return the corresponding number (1-{len(available_slots)}).
    If the user's choice is unclear or cannot be understood, return 0.

    ## Output Format
    Return the result in **JSON format** and the slot_selected should be an number only
    **Example Output:**
    {{
    "slot_selected": 2,
    }}
    """

    @staticmethod
    def confirmation_prompt(entities: Dict[str, Any], selected_slot: Dict[str, Any]) -> str:
        """Generate a friendly and professional confirmation message for the appointment."""
        patient_name = entities.get('patient_info', {}).get('name', "未提供")
        appointment_type = entities.get('appointment_type', "未提供")
        doctor_name = selected_slot.get('doctor_name', "未提供")
        specialty = selected_slot.get('specialty', "未提供")
        date = selected_slot.get('date', "未提供")
        start_time = selected_slot.get('start_time', "未提供")
        end_time = selected_slot.get('end_time', "未提供")
        phone_number = entities.get('phone_number', "未提供")
        policy_number = entities.get('policy_number', "未提供")

        return f"""
    ## Task
    Please generate a friendly and professional appointment confirmation message that includes the following information:

    Appointment Information:
    - Patient Name: {patient_name}
    - Appointment Type: {appointment_type}
    - Doctor: {doctor_name} ({specialty})
    - Time: {date} {start_time}-{end_time}
    - Phone Number: {phone_number}
    - Policy Number: {policy_number}

    Please ensure the message:
    1. Is written in Traditional Chinese.
    2. Is friendly and professional.
    3. Clearly asks the user to confirm the appointment.

    ## Output Format
    Return the result in **JSON format**.
    **Example Output:**
    {{
    "confirmation_message": "
    您的預約已確認！以下是您的預約信息：

    - 病人姓名: {patient_name}
    - 預約類型: {appointment_type}
    - 醫生: {doctor_name} ({specialty})
    - 時間: {date} {start_time}-{end_time}
    - 電話號碼: {phone_number}
    - 保單號碼: {policy_number}

    請確認以上信息是否正確。如有問題，請隨時聯繫我們。
    "
    }}
    """

class LLMService:
    """
    LLM Service - Responsibilities:
    - Coordinate all LLM operations using GeminiService and PromptTemplates
    - Extract entities from user messages
    - Generate appropriate follow-up questions
    - Handle slot selection logic
    - Generate confirmation messages
    - Provide high-level interface for conversation management
    """
    
    def __init__(self):
        self.gemini = GeminiService()
        self.templates = PromptTemplates()
        
    def extract_entities(self, user_message: str, current_entities: Dict[str, Any], conversation_context: str = "") -> Dict[str, Any]:
        """ Extract entities from user message using LLM."""
        prompt = self.templates.entity_extraction_prompt(user_message, current_entities, conversation_context)
        response = self.gemini.generate_response(prompt)
        
        if not response:
            return {}
            
        try:
            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                entities = json.loads(json_str)
                return entities
            else:
                print(f"No JSON found in response: {response}")
                return {}
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}, Response: {response}")
            return {}
    
    def generate_missing_fields_question(self, missing_fields: List[str], conversation_context: str, current_entities: Dict[str, Any]) -> str:
        """ Generate a question asking for missing fields. """
        prompt = self.templates.missing_fields_prompt(missing_fields, conversation_context, current_entities)
        response = self.gemini.generate_response(prompt)
        
        return response or "请提供您的预约信息，我来帮您安排。"
    
    def parse_slot_selection(self, user_message: str, available_slots: List[Dict[str, Any]]) -> int:
        """ Parse user's time slot selection. """
        if not available_slots:
            return 0
            
        prompt = self.templates.slot_selection_prompt(user_message, available_slots)
        response = self.gemini.generate_response(prompt)
        
        if not response:
            return 0
            
        try:
            selection = int(response.strip())
            if 1 <= selection <= len(available_slots):
                return selection
            else:
                return 0
        except ValueError:
            return 0
    
    def generate_confirmation_message(self, entities: Dict[str, Any], selected_slot: Dict[str, Any]) -> str:
        """ Generate appointment confirmation message """
        prompt = self.templates.confirmation_prompt(entities, selected_slot)
        response = self.gemini.generate_response(prompt)
        
        return response or "请确认您的预约信息是否正确？"
    
    def generate_greeting(self) -> str:
        """ Generate greeting message """
        return "您好！欢迎使用智能预约系统。我可以帮您预约医生。请告诉我您的预约需求。"