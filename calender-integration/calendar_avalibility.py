import os
import pickle
import datetime
import pytz
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# -------- CONFIG --------
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TIMEZONE = 'Asia/Hong_Kong'
SUGGESTION_DURATION_MINUTES = 60
BUSINESS_HOURS_START = 9  # 9 AM
BUSINESS_HOURS_END = 18   # 6 PM


def get_authenticated_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('calendar', 'v3', credentials=creds)


def get_all_calendar_ids(service):
    calendar_list = service.calendarList().list().execute()
    for entry in calendar_list['items']:
        print(f"ID: {entry['id']} | Summary: {entry['summary']}")
    return [entry['id'] for entry in calendar_list['items'] if not entry.get('deleted', False)]


def get_free_busy(service, time_min, time_max):
    all_calendar_ids = get_all_calendar_ids(service)
    body = {
        "timeMin": time_min.isoformat(),
        "timeMax": time_max.isoformat(),
        "timeZone": TIMEZONE,
        "items": [{"id": cal_id} for cal_id in all_calendar_ids]
    }
    return service.freebusy().query(body=body).execute()


def parse_busy_times(freebusy_response):
    busy_periods = []
    for cal_id, data in freebusy_response['calendars'].items():
        busy_periods.extend(data.get('busy', []))
    return [
        (datetime.datetime.fromisoformat(b['start']), datetime.datetime.fromisoformat(b['end']))
        for b in busy_periods
    ]


def suggest_meeting_times(busy_periods, time_min, time_max):
    tz = pytz.timezone(TIMEZONE)
    time_min = time_min.astimezone(tz)
    time_max = time_max.astimezone(tz)

    # Round to the next full hour
    if time_min.minute > 0 or time_min.second > 0 or time_min.microsecond > 0:
        time_min = (time_min + datetime.timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)

    current = time_min
    suggestions = []
    slot_duration = datetime.timedelta(minutes=SUGGESTION_DURATION_MINUTES)

    while current + slot_duration <= time_max:
        hour = current.hour
        # Only consider slots within business hours
        if BUSINESS_HOURS_START <= hour < BUSINESS_HOURS_END:
            overlap = False
            for busy_start, busy_end in busy_periods:
                # Ensure busy periods are timezone-aware
                if busy_start.tzinfo is None:
                    busy_start = tz.localize(busy_start)
                else:
                    busy_start = busy_start.astimezone(tz)
                if busy_end.tzinfo is None:
                    busy_end = tz.localize(busy_end)
                else:
                    busy_end = busy_end.astimezone(tz)

                if (busy_start < current + slot_duration) and (busy_end > current):
                    overlap = True
                    break
            if not overlap:
                suggestions.append(current)
        current += slot_duration
    return suggestions




def main():
    service = get_authenticated_service()

    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)
    later = now + datetime.timedelta(hours=24)

    freebusy_result = get_free_busy(service, now, later)
    busy_periods = parse_busy_times(freebusy_result)

    print("\n⛔ Busy Periods (Hong Kong Time):")
    for start, end in busy_periods:
        start_hk = start.astimezone(tz)
        end_hk = end.astimezone(tz)
        print(f"{start_hk.strftime('%Y-%m-%d %H:%M')} to {end_hk.strftime('%Y-%m-%d %H:%M')}")

    print(f"\n✅ Suggested Office Hour Available {SUGGESTION_DURATION_MINUTES}-min Time Slots (Hong Kong Time):")
    suggested = suggest_meeting_times(busy_periods, now, later)
    for time in suggested:
        print(time.strftime('%Y-%m-%d %H:%M'))


if __name__ == '__main__':
    main()
