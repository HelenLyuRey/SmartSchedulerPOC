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



def get_events(service, time_min, time_max):
    """
    Fetch all events within the specified time range and categorize them as 'Free' or 'Busy'.
    """
    tz = pytz.timezone(TIMEZONE)
    time_min = time_min.astimezone(tz).isoformat()
    time_max = time_max.astimezone(tz).isoformat()

    all_calendar_ids = get_all_calendar_ids(service)
    free_periods = []
    busy_periods = []

    for cal_id in all_calendar_ids:
        events_result = service.events().list(
            calendarId=cal_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        for event in events:
            start = event['start'].get('dateTime')
            end = event['end'].get('dateTime')
            transparency = event.get('transparency', 'opaque')  # Default to 'opaque' if not specified

            if start and end:
                start_dt = datetime.datetime.fromisoformat(start)
                end_dt = datetime.datetime.fromisoformat(end)

                if transparency == 'transparent':  # Free event
                    free_periods.append((start_dt, end_dt))
                else:  # Busy event
                    busy_periods.append((start_dt, end_dt))

    return free_periods, busy_periods


def main():
    service = get_authenticated_service()

    tz = pytz.timezone(TIMEZONE)
    now = datetime.datetime.now(tz)

    # Calculate the start and end of the current week (Monday to Friday)
    start_of_week = now - datetime.timedelta(days=now.weekday())  # Monday
    end_of_week = start_of_week + datetime.timedelta(days=4, hours=23, minutes=59, seconds=59)  # Friday

    # Ensure timezone awareness
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=0)

    free_periods, busy_periods = get_events(service, start_of_week, end_of_week)

    print("\n⛔ Busy Periods (Hong Kong Time):")
    print(busy_periods)
    for start, end in busy_periods:
        start_hk = start.astimezone(tz)
        end_hk = end.astimezone(tz)
        print(f"{start_hk.strftime('%Y-%m-%d %H:%M')} to {end_hk.strftime('%Y-%m-%d %H:%M')}")

    print(f"\n✅ Free Periods (Hong Kong Time):")
    print(free_periods)
    for start, end in free_periods:
        start_hk = start.astimezone(tz)
        end_hk = end.astimezone(tz)
        print(f"{start_hk.strftime('%Y-%m-%d %H:%M')} to {end_hk.strftime('%Y-%m-%d %H:%M')}")


if __name__ == '__main__':
    main()