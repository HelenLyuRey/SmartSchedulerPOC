"""
Calendar Service - Enhanced to parse doctor availability from calendar events
"""

import datetime
import pytz
from typing import List, Dict, Any, Optional
from models import DoctorSlot
from config import MOCK_DOCTORS

try:
    from calendar_avalibility import (
        get_authenticated_service,
        TIMEZONE
    )
    CALENDAR_AVAILABLE = True
except ImportError:
    print("Calendar module not available, using mock data")
    CALENDAR_AVAILABLE = False
    TIMEZONE = 'Asia/Hong_Kong'

class EnhancedCalendarService:
    """
    Enhanced Calendar Service - Parses doctor availability from calendar events
    """
    
    def __init__(self, use_mock: bool = False):
        self.use_mock = use_mock or not CALENDAR_AVAILABLE
        self.tz = pytz.timezone(TIMEZONE)
        
        if not self.use_mock:
            try:
                self.service = get_authenticated_service()
            except Exception as e:
                print(f"Failed to connect to Google Calendar: {e}")
                self.use_mock = True
    
    def get_doctor_availability_events(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Get calendar events that represent doctor availability
        Looks for events with "Available" in the title
        """
        if self.use_mock:
            return self._get_mock_availability_events(days_ahead)
        
        try:
            now = datetime.datetime.now(self.tz)
            time_min = now.isoformat()
            time_max = (now + datetime.timedelta(days=days_ahead)).isoformat()
            
            # Get all events from primary calendar
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Filter for availability events
            availability_events = []
            for event in events:
                summary = event.get('summary', '').lower()
                if 'available' in summary or 'avail' in summary:
                    availability_events.append(event)
            
            return availability_events
            
        except Exception as e:
            print(f"Error getting calendar events: {e}")
            return self._get_mock_availability_events(days_ahead)
    
    def _get_mock_availability_events(self, days_ahead: int) -> List[Dict[str, Any]]:
        """Generate mock availability events"""
        events = []
        base_date = datetime.datetime.now(self.tz)
        
        # Generate mock events for next few days
        for day_offset in range(1, min(days_ahead + 1, 4)):
            current_date = base_date + datetime.timedelta(days=day_offset)
            
            mock_events = [
                {
                    'summary': 'Dr. Wang Available - Internal Medicine',
                    'start': {'dateTime': current_date.replace(hour=9, minute=0).isoformat()},
                    'end': {'dateTime': current_date.replace(hour=10, minute=0).isoformat()},
                    'description': 'Available for appointments'
                },
                {
                    'summary': 'Dr. Li Available - Surgery',
                    'start': {'dateTime': current_date.replace(hour=14, minute=0).isoformat()},
                    'end': {'dateTime': current_date.replace(hour=15, minute=0).isoformat()},
                    'description': 'Available for appointments'
                },
                {
                    'summary': 'Dr. Zhang Available - Pediatrics',
                    'start': {'dateTime': current_date.replace(hour=16, minute=0).isoformat()},
                    'end': {'dateTime': current_date.replace(hour=17, minute=0).isoformat()},
                    'description': 'Available for appointments'
                },
                {
                    'summary': 'Dr. Wang BUSY - Meeting',
                    'start': {'dateTime': current_date.replace(hour=11, minute=0).isoformat()},
                    'end': {'dateTime': current_date.replace(hour=12, minute=0).isoformat()},
                    'description': 'Not available'
                }
            ]
            events.extend(mock_events)
        
        return events
    
    def parse_doctor_info_from_event(self, event: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        Parse doctor information from calendar event title
        Expected format: "Dr. [Name] Available - [Specialty]"
        """
        summary = event.get('summary', '')
        
        # Skip if not an availability event
        if 'available' not in summary.lower():
            return None
        
        try:
            # Parse "Dr. Wang Available - Internal Medicine"
            parts = summary.split(' - ')
            if len(parts) >= 2:
                doctor_part = parts[0].strip()  # "Dr. Wang Available"
                specialty = parts[1].strip()    # "Internal Medicine"
                
                # Extract doctor name
                doctor_name = doctor_part.replace('Available', '').replace('AVAILABLE', '').strip()
                
                # Generate doctor ID
                doctor_id = doctor_name.lower().replace(' ', '_').replace('.', '')
                
                return {
                    'doctor_id': doctor_id,
                    'doctor_name': doctor_name,
                    'specialty': specialty
                }
        except Exception as e:
            print(f"Error parsing doctor info from '{summary}': {e}")
        
        return None
    
    def convert_events_to_slots(self, events: List[Dict[str, Any]]) -> List[DoctorSlot]:
        """Convert calendar events to DoctorSlot objects"""
        slots = []
        
        for event in events:
            doctor_info = self.parse_doctor_info_from_event(event)
            if not doctor_info:
                continue
            
            # Parse event time
            start_time = event['start'].get('dateTime')
            end_time = event['end'].get('dateTime')
            
            if not start_time or not end_time:
                continue
            
            try:
                start_dt = datetime.datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                
                # Convert to local timezone
                start_local = start_dt.astimezone(self.tz)
                end_local = end_dt.astimezone(self.tz)
                
                slot = DoctorSlot(
                    doctor_id=doctor_info['doctor_id'],
                    doctor_name=doctor_info['doctor_name'],
                    specialty=doctor_info['specialty'],
                    date=start_local.strftime("%Y-%m-%d"),
                    start_time=start_local.strftime("%H:%M"),
                    end_time=end_local.strftime("%H:%M"),
                    available=True
                )
                slots.append(slot)
                
            except Exception as e:
                print(f"Error converting event to slot: {e}")
                continue
        
        return slots
    
    def get_available_slots(self, 
                          target_date: str = None, 
                          time_preference: str = None,
                          days_ahead: int = 7) -> List[DoctorSlot]:
        """Get available appointment slots from calendar events"""
        
        # Get availability events from calendar
        events = self.get_doctor_availability_events(days_ahead)
        
        # Convert to slots
        all_slots = self.convert_events_to_slots(events)
        
        # Filter by preferences
        filtered_slots = []
        for slot in all_slots:
            # Filter by date
            if target_date and not self._matches_target_date(slot.date, target_date):
                continue
            
            # Filter by time preference
            if time_preference and not self._matches_time_preference(slot, time_preference):
                continue
            
            filtered_slots.append(slot)
        
        return filtered_slots
    
    def _matches_target_date(self, slot_date: str, target_date: str) -> bool:
        """Check if slot date matches target preference"""
        if not target_date:
            return True
        
        # Handle relative dates
        today = datetime.datetime.now(self.tz)
        if "明天" in target_date:
            tomorrow = (today + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
            return slot_date == tomorrow
        elif "今天" in target_date:
            today_str = today.strftime("%Y-%m-%d")
            return slot_date == today_str
        
        # Handle specific dates
        return target_date in slot_date
    
    def _matches_time_preference(self, slot: DoctorSlot, time_preference: str) -> bool:
        """Check if slot time matches preference"""
        if not time_preference:
            return True
        
        hour = int(slot.start_time.split(':')[0])
        
        if time_preference == "上午":
            return 9 <= hour < 12
        elif time_preference == "下午":
            return 12 <= hour < 18
        elif time_preference == "晚上":
            return 18 <= hour < 21
        
        return True
    
    def format_slots_for_display(self, slots: List[DoctorSlot]) -> str:
        """Format slots for user display"""
        if not slots:
            return "抱歉，目前沒有符合您需求的預約時間。"
        
        display_text = "以下是可用的預約時間：\n\n"
        
        for i, slot in enumerate(slots, 1):
            display_text += f"{i}. {slot.doctor_name} ({slot.specialty})\n"
            display_text += f"   📅 {slot.date} {slot.start_time}-{slot.end_time}\n\n"
        
        display_text += "請告訴我您想選擇第幾個時間段。"
        return display_text