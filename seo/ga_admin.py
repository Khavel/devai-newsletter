"""GA4 Admin API helper — list / verify / create properties + web data streams.

Auth: service account JSON key. Put it at seo/.gcp-sa.json (gitignored) OR set
GOOGLE_APPLICATION_CREDENTIALS to its path. The service account email must be
added to the GA *account* as Administrator (Admin -> Account Access Management).

Usage:
  python ga_admin.py list
      List every account, its properties, web streams, and Measurement IDs.

  python ga_admin.py ensure --account 123456789 --name "DevAI Semanal" \
      --domain devaisemanal.com [--timezone Europe/Madrid] [--currency EUR]
      Find-or-create a property by display name under the account, then
      find-or-create a WEB data stream for the domain. Prints the Measurement ID.
      Idempotent: re-running never duplicates; it reuses matches by name/domain.

  python ga_admin.py keyevents --property 539660132
      List every Key Event (conversion event) configured on a property.

  python ga_admin.py keyevent --property 539660132 --event sign_up
      Find-or-create a Key Event for the given event name (idempotent: if the
      event is already a key event it is left untouched). This is the KPI's
      measurement primitive for DevAI Semanal (the Ghost portal signup fires
      `sign_up`). NOTE: this only marks an *already-collected* event as a key
      event; the event itself must be emitted by the site (Ghost portal form
      submit) — GA4 cannot synthesize an event that the site never sends.

Scope used: analytics.edit (read + write config). No data is ever deleted.
"""
import sys, os, argparse
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

# NOTE: Pi-hole on Firebat (192.168.1.21) used to blackhole analytics*.googleapis.com
# to 0.0.0.0 (they're on the Hagezi tracker blocklist). Fixed network-wide via:
#   docker exec pihole pihole allow analyticsadmin.googleapis.com
#   docker exec pihole pihole allow analyticsdata.googleapis.com
# If the API ever fails DNS again, re-run those on Firebat.

from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as UserCredentials
import google.auth.transport.requests as _gtr
from google.analytics.admin import AnalyticsAdminServiceClient
from google.analytics.admin_v1alpha import Property, DataStream

SCOPES = ["https://www.googleapis.com/auth/analytics.edit"]
HERE = Path(__file__).parent
DEFAULT_KEY = HERE / ".gcp-sa.json"
OAUTH_TOKEN = HERE / ".ga-oauth-token.json"   # user OAuth (preferred; GA blocks SA emails)


def client():
    # Prefer user OAuth (real account owns the properties; no GA "add user" needed).
    if OAUTH_TOKEN.exists():
        creds = UserCredentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
        if not creds.valid and creds.refresh_token:
            creds.refresh(_gtr.Request())
            OAUTH_TOKEN.write_text(creds.to_json(), encoding="utf-8")
        print("auth: user OAuth (.ga-oauth-token.json)")
        return AnalyticsAdminServiceClient(credentials=creds, transport="rest")
    # Fallback: service account (only works if GA accepts the SA email as a user).
    key = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "").strip() or str(DEFAULT_KEY)
    if not Path(key).exists():
        sys.exit("ERROR: no credentials. Run  python seo/_ga_oauth.py  to create "
                 f"{OAUTH_TOKEN.name}, or place a service-account key at {DEFAULT_KEY}.")
    creds = service_account.Credentials.from_service_account_file(key, scopes=SCOPES)
    print(f"auth: service account {creds.service_account_email}")
    return AnalyticsAdminServiceClient(credentials=creds, transport="rest")


def norm_domain(d):
    return d.lower().replace("https://", "").replace("http://", "").rstrip("/").removeprefix("www.")


def list_all(c):
    summaries = list(c.list_account_summaries())
    if not summaries:
        print("\n(no accounts visible to this service account — is it added as an "
              "account user with Administrator/Editor role?)")
        return
    for s in summaries:
        print(f"\n=== ACCOUNT {s.account}  «{s.display_name}»")
        if not s.property_summaries:
            print("   (no properties)")
        for p in s.property_summaries:
            pid = p.property.split('/')[-1]
            print(f"  - PROPERTY {pid}  «{p.display_name}»")
            for ds in c.list_data_streams(parent=p.property):
                w = ds.web_stream_data
                if w and w.measurement_id:
                    print(f"        WEB  {w.measurement_id:14}  {w.default_uri}   (stream «{ds.display_name}»)")
                else:
                    print(f"        {DataStream.DataStreamType(ds.type_).name}  «{ds.display_name}»")


def ensure(c, account, name, domain, timezone, currency):
    acc = f"accounts/{account}"
    # find property by display name under this account
    prop = None
    for s in c.list_account_summaries():
        if s.account != acc:
            continue
        for p in s.property_summaries:
            if p.display_name.strip().lower() == name.strip().lower():
                prop = p.property
                print(f"found existing property: {prop} «{p.display_name}»")
                break
    if not prop:
        created = c.create_property(property=Property(
            parent=acc, display_name=name, time_zone=timezone, currency_code=currency))
        prop = created.name
        print(f"CREATED property: {prop} «{name}» (tz={timezone}, cur={currency})")

    # find web stream by domain
    want = norm_domain(domain)
    for ds in c.list_data_streams(parent=prop):
        w = ds.web_stream_data
        if w and w.default_uri and norm_domain(w.default_uri) == want:
            print(f"found existing web stream: {w.default_uri}")
            print(f"\n>>> MEASUREMENT ID: {w.measurement_id}\n")
            return w.measurement_id
    created = c.create_data_stream(parent=prop, data_stream=DataStream(
        type_=DataStream.DataStreamType.WEB_DATA_STREAM,
        display_name=name,
        web_stream_data=DataStream.WebStreamData(default_uri=f"https://{want}")))
    mid = created.web_stream_data.measurement_id
    print(f"CREATED web stream: https://{want}")
    print(f"\n>>> MEASUREMENT ID: {mid}\n")
    return mid


def set_retention(c, months=14):
    """Set event-data retention to its max for every property the user can see.
    Free GA4 max is 14 months (default is a mere 2). Also enables reset-on-activity."""
    from google.analytics.admin_v1alpha import DataRetentionSettings
    from google.protobuf.field_mask_pb2 import FieldMask
    dur = {14: DataRetentionSettings.RetentionDuration.FOURTEEN_MONTHS,
           2:  DataRetentionSettings.RetentionDuration.TWO_MONTHS}[months]
    from google.api_core.exceptions import PermissionDenied, Forbidden
    for s in c.list_account_summaries():
        for p in s.property_summaries:
            try:
                cur = c.get_data_retention_settings(name=f"{p.property}/dataRetentionSettings")
                if cur.event_data_retention == dur:
                    print(f"SKIP «{p.display_name}» already {cur.event_data_retention.name}")
                    continue
                upd = c.update_data_retention_settings(
                    data_retention_settings=DataRetentionSettings(
                        name=f"{p.property}/dataRetentionSettings",
                        event_data_retention=dur,
                        reset_user_data_on_new_activity=True),
                    update_mask=FieldMask(paths=["event_data_retention",
                                                 "reset_user_data_on_new_activity"]))
                print(f"SET «{p.display_name}» -> {upd.event_data_retention.name}")
            except (PermissionDenied, Forbidden):
                print(f"SKIP «{p.display_name}» (not editable by this user)")


def list_key_events(c, prop):
    parent = prop if str(prop).startswith("properties/") else f"properties/{prop}"
    print(f"=== KEY EVENTS for {parent}")
    any_ = False
    for ke in c.list_key_events(parent=parent):
        any_ = True
        print(f"  - {ke.event_name!r:24} counting={ke.counting_method.name:16} "
              f"custom={ke.custom}  deletable={ke.deletable}")
    if not any_:
        print("  (none configured)")


def ensure_key_event(c, prop, event):
    """Find-or-create a key event by event name. Idempotent."""
    from google.analytics.admin_v1alpha import KeyEvent
    parent = prop if str(prop).startswith("properties/") else f"properties/{prop}"
    for ke in c.list_key_events(parent=parent):
        if ke.event_name == event:
            print(f"found existing key event: {event!r} "
                  f"(counting={ke.counting_method.name}, custom={ke.custom})")
            return ke.name
    created = c.create_key_event(
        parent=parent,
        key_event=KeyEvent(
            event_name=event,
            counting_method=KeyEvent.CountingMethod.ONCE_PER_EVENT))
    print(f"CREATED key event: {event!r} -> {created.name}")
    print("  NOTE: this only marks the event as a conversion; the site must "
          "actually emit it for it to count.")
    return created.name


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sub.add_parser("retention")  # bump all properties to 14-month retention
    e = sub.add_parser("ensure")
    e.add_argument("--account", required=True, help="GA account ID (digits only)")
    e.add_argument("--name", required=True, help="property display name")
    e.add_argument("--domain", required=True, help="e.g. devaisemanal.com")
    e.add_argument("--timezone", default="Europe/Madrid")
    e.add_argument("--currency", default="EUR")
    ke = sub.add_parser("keyevents")   # list key events on a property
    ke.add_argument("--property", required=True, help="GA4 property ID (digits)")
    kc = sub.add_parser("keyevent")    # find-or-create one key event
    kc.add_argument("--property", required=True, help="GA4 property ID (digits)")
    kc.add_argument("--event", required=True, help="event name, e.g. sign_up")
    a = ap.parse_args()
    c = client()
    if a.cmd == "list":
        list_all(c)
    elif a.cmd == "retention":
        set_retention(c)
    elif a.cmd == "keyevents":
        list_key_events(c, a.property)
    elif a.cmd == "keyevent":
        ensure_key_event(c, a.property, a.event)
    else:
        ensure(c, a.account, a.name, a.domain, a.timezone, a.currency)


if __name__ == "__main__":
    main()
