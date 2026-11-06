from flask import Flask, request, jsonify
import uuid
from datetime import datetime, timedelta, timezone
import os.path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

app = Flask(__name__)

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']


# ✅ Create REAL Google Meet link
def create_meet_link():
    creds = None

    # Load saved token (so login not required every time)
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If no valid credentials → login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # Save credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    now = datetime.now(timezone.utc)

    event = {
        'summary': 'Slack Meeting',
        'start': {
            'dateTime':  now.isoformat(),
            'timeZone': 'Australia/Sydney',
        },
        'end': {
            'dateTime': (now + timedelta(hours=1)).isoformat(),
            'timeZone': 'Australia/Sydney',
        },
        'conferenceData': {
            'createRequest': {
                'requestId': str(uuid.uuid4()),
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                }
            }
        }
    }

    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    return event.get('hangoutLink')


# ✅ Optional root route
@app.route('/')
def home():
    return "Slack bot is running ✅"


# ✅ Slack Slash Command endpoint
@app.route('/meeting', methods=['POST'])
def meeting():
    user = request.form.get('user_name')

    try:
        link = create_meet_link()

        return jsonify({
            "response_type": "in_channel",
            "text": f"{user} created a Google Meet: {link}"
        })

    except Exception as e:
        return jsonify({
            "response_type": "ephemeral",
            "text": f"❌ Error creating meeting: {str(e)}"
        })


if __name__ == '__main__':
    app.run(port=3000)