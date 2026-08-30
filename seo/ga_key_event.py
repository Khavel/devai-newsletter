"""GA4 Key Event helper — list / ensure a key event (conversion) on a property.

ga_admin.py only does properties + streams; this fills the gap. Marks an event
(e.g. `sign_up`) as a KEY EVENT so GA4 counts it as a conversion in reports.

Auth: reuses the same user OAuth token as ga_admin.py (.ga-oauth-token.json,
scope analytics.edit). No service account needed.

Usage:
  python ga_key_event.py list   --property 539660132
  python ga_key_event.py ensure --property 539660132 --event sign_up

Idempotent: `ensure` is a no-op if the key event already exists.
"""
import sys, argparse
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

from google.oauth2.credentials import Credentials as UserCredentials
import google.auth.transport.requests as _gtr
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha import KeyEvent

SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]
HERE = Path(__file__).parent
OAUTH_TOKEN = HERE / ".ga-oauth-token.json"


def client():
    if not OAUTH_TOKEN.exists():
        sys.exit(f"ERROR: no OAuth token at {OAUTH_TOKEN}. Run the GA OAuth flow first.")
    creds = UserCredentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
    if not creds.valid and creds.refresh_token:
        creds.refresh(_gtr.Request())
        OAUTH_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print("auth: user OAuth (.ga-oauth-token.json)")
    return AnalyticsAdminServiceClient(credentials=creds, transport="rest")


def list_key_events(c, prop):
    parent = f"properties/{prop}"
    found = list(c.list_key_events(parent=parent))
    if not found:
        print(f"(no key events on property {prop})")
        return found
    print(f"key events on property {prop}:")
    for k in found:
        print(f"  - {k.event_name}   (deletable={k.deletable}, custom={k.custom}, "
              f"counting={k.counting_method.name if k.counting_method else 'n/a'})")
    return found


def ensure(c, prop, event):
    parent = f"properties/{prop}"
    for k in c.list_key_events(parent=parent):
        if k.event_name == event:
            print(f"OK: key event '{event}' already exists on property {prop} — no change.")
            return k
    created = c.create_key_event(parent=parent, key_event=KeyEvent(event_name=event))
    print(f"CREATED key event '{event}' on property {prop}: {created.name}")
    return created


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "ensure"):
        p = sub.add_parser(name)
        p.add_argument("--property", required=True, help="GA4 property ID (digits only)")
        if name == "ensure":
            p.add_argument("--event", required=True, help="event name, e.g. sign_up")
    a = ap.parse_args()
    c = client()
    if a.cmd == "list":
        list_key_events(c, a.property)
    else:
        ensure(c, a.property, a.event)


if __name__ == "__main__":
    main()
