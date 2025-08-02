# Google Calendar Availability & Booking API (Python FastAPI POC)

This is a simple proof-of-concept project for integrating with the **Google Calendar API** using Python.

It includes:

- ✅ Authentication and calendar event reading  
- 🧠 Smart time slot suggestion (skip mornings, avoid lunch hours, etc.)  
- 📅 Event booking via FastAPI  
- 🔌 API endpoints for use in apps, bots, or scheduling tools  



## Requirements

### `requirements.txt`

Install dependencies via:

```bash
pip install -r requirements.txt
```


## Setup

### 1. Enable Google Calendar API

- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project
- Navigate to: **APIs & Services > Library**
- Enable **Google Calendar API**

### 2. Create OAuth 2.0 Credentials

- Go to **APIs & Services > Credentials**
- Click **Create Credentials** > **OAuth client ID**
- If prompted:
  - Set the app type to **Desktop App**
  - Name it e.g., `Calendar POC`
- Download the `credentials.json` file and place it in your project root

> 📌 **IMPORTANT**: Add your Gmail to the **Test Users** section under **OAuth Consent Screen** to avoid `403: access_denied` error  
Go to **OAuth consent screen > Audience > Test users > Add your email**


### 3. How Authentication Works

- The first time you run a script, it opens a browser for you to sign in with Google
- If successful, a `token.pickle` file will be created to store access/refresh tokens
- On future runs, this token is reused, so you won’t need to re-authenticate

> 🔐 `token.pickle` = your personal access token, **do not commit to Git**


## Running the Scripts

### `calendar_availability.py` (CLI Script)

This script prints:
- Busy times from your primary calendar (based on your timezone)
- Suggest meeting slots only within business hours

#### Run it:

``` bash
python calendar_availability.py
```

#### Expected output:

``` bash
⛔ Busy Periods (Hong Kong Time):
2025-08-03 09:00 to 2025-08-03 11:00

✅ Suggested Office Hour Available 60-min Time Slots (Hong Kong Time):
2025-08-03 11:00
2025-08-03 12:00
2025-08-03 13:00
2025-08-03 14:00
2025-08-03 15:00
2025-08-03 16:00
2025-08-03 17:00
```
![alt text](image.png)


### `calendar_api_poc.py` (FastAPI Server)

#### Run it:

```bash
uvicorn calendar_api_poc:app --reload
```

#### API Endpoints:

##### `GET /suggest`

Suggests free 30-min time slots (with smart filtering).

Example:

```bash
GET http://127.0.0.1:8000/suggest?days=2&only_afternoon=true&exclude_lunch=true
```

Query Params:
- `days`: (default 3) how many days to search
- `only_afternoon`: skip times before 2PM
- `exclude_lunch`: skip 12–2PM


##### `POST /book`

Creates a Google Calendar event.

Example request:

```
POST http://127.0.0.1:8000/book
Content-Type: application/json

{
  "title": "POC Calendar Test",
  "start_time": "2025-08-04T15:00:00",
  "end_time": "2025-08-04T15:30:00",
  "description": "Test booking from FastAPI",
  "attendees": ["your.email@gmail.com"]
}
```

Successful response:

```bash
{
  "success": true,
  "event_link": "https://www.google.com/calendar/event?eid=abc123..."
}
```


## Smart Suggestion Logic

The suggestion logic uses:
- Working hours: 9:00 AM – 6:00 PM
- Optional filters:
  - Skip lunch (12:00 PM – 2:00 PM)
  - Only suggest after 2:00 PM
- Avoids overlaps with any existing busy events in your calendar



## Notes

- This project is for personal/dev use only. For production apps, you’ll need to complete **OAuth app verification** with Google.
- Be careful with rate limits if calling the API frequently.
- Do not commit your `token.pickle` or `credentials.json` to public repositories.


## TODOs & Extensions

Want to build further?

- Auto-generate Google Meet link
- Add API key/auth for public deployment
- Add priority rules (e.g. prefer mornings or even slots)
- Integrate with Slack/WhatsApp bot for real-time booking
- Deploy to cloud (e.g., Vercel, Azure App Service)


## Credits

Built using:
- [FastAPI](https://fastapi.tiangolo.com/)
- [Google Calendar API](https://developers.google.com/calendar/api)
- [google-api-python-client](https://github.com/googleapis/google-api-python-client)

