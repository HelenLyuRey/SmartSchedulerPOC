from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import datetime
import pytz

from calendar_avalibility import ( 
    get_authenticated_service,
    get_free_busy,
    parse_busy_times,
    suggest_meeting_times,
    TIMEZONE
)

app = FastAPI()


class TimeRangeRequest(BaseModel):
    hours_ahead: int = 24  # Default to next 24 hours


class TimeSlot(BaseModel):
    start: str
    end: str


class SuggestionResponse(BaseModel):
    busy_periods: List[TimeSlot]
    suggested_times: List[str]


@app.post("/calendar/suggest", response_model=SuggestionResponse)
async def suggest_times(request: TimeRangeRequest):
    service = get_authenticated_service()
    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    later = now + datetime.timedelta(hours=request.hours_ahead)

    freebusy_result = get_free_busy(service, now, later)
    busy_periods = parse_busy_times(freebusy_result)
    suggested = suggest_meeting_times(busy_periods, now, later)

    busy_list = [
        {"start": start.astimezone(tz).strftime('%Y-%m-%d %H:%M'),
         "end": end.astimezone(tz).strftime('%Y-%m-%d %H:%M')}
        for start, end in busy_periods
    ]
    suggested_list = [time.strftime('%Y-%m-%d %H:%M') for time in suggested]

    return SuggestionResponse(busy_periods=busy_list, suggested_times=suggested_list)
