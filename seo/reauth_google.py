"""One-shot Google OAuth re-auth for the marketing hub's read collectors.

Re-consents to BOTH scopes in a single Google sign-in and writes the two token
files the GA4 + GSC collectors read:
  - seo/.ga-adc.json          (ADC "authorized_user" format; GA4 BetaAnalyticsDataClient)
  - ../token-webmasters.json  (google.oauth2 authorized-user json; GSC searchAnalytics)

Run it, complete the Google consent in the browser (pick the account that has
BOTH the GA4 properties and Search Console), and both collectors come back to life.

Usage:  python reauth_google.py
"""
import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SEO = Path(__file__).resolve().parent
ROOT = SEO.parent  # devai-newsletter
CLIENT = ROOT / "gsc-oauth-client.json"          # existing desktop OAuth client
GA_ADC = SEO / ".ga-adc.json"                     # GA4 collector (GOOGLE_APPLICATION_CREDENTIALS)
GSC_TOKEN = ROOT / "token-webmasters.json"        # GSC collector

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly",  # GA4 read
    "https://www.googleapis.com/auth/webmasters",          # Search Console
]


def main():
    if not CLIENT.exists():
        print(f"ERROR: OAuth client not found at {CLIENT}")
        sys.exit(2)

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    # run_local_server prints the auth URL, opens the browser, and waits on a
    # localhost callback. Any browser that hits the printed localhost URL completes it.
    creds = flow.run_local_server(port=0, prompt="consent", open_browser=True,
                                  authorization_prompt_message="VISIT_THIS_URL: {url}")

    full = json.loads(creds.to_json())  # token/refresh_token/client_id/client_secret/scopes/...

    # GSC: google.oauth2 Credentials.from_authorized_user_file accepts to_json() shape.
    GSC_TOKEN.write_text(json.dumps(full), encoding="utf-8")

    # GA4 ADC: GOOGLE_APPLICATION_CREDENTIALS needs the "authorized_user" ADC shape.
    adc = {
        "type": "authorized_user",
        "client_id": full.get("client_id"),
        "client_secret": full.get("client_secret"),
        "refresh_token": full.get("refresh_token"),
    }
    GA_ADC.write_text(json.dumps(adc), encoding="utf-8")

    print("OK: wrote", GA_ADC.name, "and", GSC_TOKEN.name)
    print("granted_scopes:", full.get("scopes"))


if __name__ == "__main__":
    main()
