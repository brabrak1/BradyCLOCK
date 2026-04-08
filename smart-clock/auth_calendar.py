#!/usr/bin/env python3
"""
One-time OAuth2 authorization for Google Calendar.
Run this script on a machine with a browser to generate token.json.
Then copy token.json to the Pi if needed.
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "client_secret.json"
TOKEN_FILE = "token.json"


def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired token...")
        creds.refresh(Request())
    elif not creds or not creds.valid:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"Error: {CREDENTIALS_FILE} not found in current directory.")
            print("Download it from Google Cloud Console → Credentials.")
            return

        print("Opening browser for Google sign-in...")
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"Token saved to {TOKEN_FILE}")
    print("Google Calendar API is ready to use.")


if __name__ == "__main__":
    main()
