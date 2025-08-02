# calendar_api_poc.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import datetime
import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

app = FastAPI()

class MeetingRequest(BaseModel):
    title: str
    start_time: datetime.datetime
    end_time: datetime.datetime
    description: Optional[str] = None
    attendees: Optional[List[str]] = []

class SlotSuggestionRequest(BaseModel):
    days: int = 3
    only_afternoon: bool = True
    exclude_lunch: bool = True


def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


def suggest_slots(service, days=3, only_afternoon=True, exclude_lunch=True):
    now = datetime.datetime.utcnow()
    end = now + datetime.timedelta(days=days)

    time_min = now.isoformat() + 'Z'
    time_max = end.isoformat() + 'Z'

    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": "Asia/Hong_Kong",
        "items": [{"id": "primary"}]
    }

    busy_periods = service.freebusy().query(body=body).execute()['calendars']['primary']['busy']

    suggestions = []
    slot_duration = datetime.timedelta(minutes=30)
    current = now

    while current + slot_duration <= end:
        start_time = current.time()
        # Skip non-working hours
        if not datetime.time(9, 0) <= start_time <= datetime.time(18, 0):
            current += slot_duration
            continue
        # Skip lunch hours
        if exclude_lunch and datetime.time(12, 0) <= start_time <= datetime.time(14, 0):
            current += slot_duration
            continue
        # Skip morning if only_afternoon is True
        if only_afternoon and start_time < datetime.time(14, 0):
            current += slot_duration
            continue

        overlap = any(
            datetime.datetime.fromisoformat(b['start']) < current + slot_duration and
            datetime.datetime.fromisoformat(b['end']) > current
            for b in busy_periods
        )
        if not overlap:
            suggestions.append(current.strftime("%Y-%m-%d %H:%M"))
        current += slot_duration

    return suggestions[:10]


def create_event(service, req: MeetingRequest):
    event = {
        'summary': req.title,
        'description': req.description,
        'start': {
            'dateTime': req.start_time.isoformat(),
            'timeZone': 'Asia/Hong_Kong',
        },
        'end': {
            'dateTime': req.end_time.isoformat(),
            'timeZone': 'Asia/Hong_Kong',
        },
        'attendees': [{'email': email} for email in req.attendees],
    }
    created_event = service.events().insert(calendarId='primary', body=event).execute()
    return created_event.get('htmlLink')


@app.get("/suggest")
def get_suggested_slots(
    days: int = Query(3),
    only_afternoon: bool = Query(True),
    exclude_lunch: bool = Query(True)
):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    return suggest_slots(service, days=days, only_afternoon=only_afternoon, exclude_lunch=exclude_lunch)


@app.post("/book")
def book_meeting(req: MeetingRequest):
    creds = get_credentials()
    service = build('calendar', 'v3', credentials=creds)
    try:
        link = create_event(service, req)
        return {"success": True, "event_link": link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
