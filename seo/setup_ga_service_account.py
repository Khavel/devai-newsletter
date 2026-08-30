"""One-time setup: create a service account + key for the GA4 collectors so the
dashboard NEVER needs an OAuth re-auth again (service-account keys do not expire).

Run ONCE:
    cd C:\\Users\\ceja_\\Desktop\\Desarrollos\\devai-newsletter\\seo
    python setup_ga_service_account.py

A browser opens -> sign in as the Google account that owns the GA4 properties and accept
(it asks for cloud-platform + analytics.manage.users; that consent is used in-memory only and
is NOT saved to disk). The script then:
  0) enables the APIs it needs (IAM, Analytics Admin, Analytics Data) and waits to propagate
  1) creates the service account  ga4-collector@testvpn-262120.iam.gserviceaccount.com
  2) downloads its key            -> seo/.ga-service-account.json
  3) grants the SA "Viewer" on the GA4 properties (Sharpyard, Vigia, DevAI)

After this, lib/collectors/ga4.py uses the key automatically (it prefers SA_KEY). No more
weekly re-auth, and you can ignore the OAuth "Testing mode" expiry entirely for GA4.

Idempotent: safe to re-run (existing SA / bindings / enabled APIs are skipped).
"""
import base64
import sys
import time
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import AuthorizedSession

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent                       # devai-newsletter
CLIENT = ROOT / "gsc-oauth-client.json"  # existing desktop OAuth client
SA_KEY_OUT = HERE / ".ga-service-account.json"

PROJECT_ID = "testvpn-262120"
PROJECT_NUMBER = "861555918471"
SA_ACCOUNT_ID = "ga4-collector"
SA_EMAIL = f"{SA_ACCOUNT_ID}@{PROJECT_ID}.iam.gserviceaccount.com"
GA4_PROPERTIES = {
    "540206942": "Sharpyard",
    "542465395": "Vigia DPO",
    "539660132": "DevAI Semanal",
}
NEEDED_APIS = [
    "iam.googleapis.com",            # create service account + key
    "analyticsadmin.googleapis.com",  # share GA4 properties
    "analyticsdata.googleapis.com",   # the collector reads via the Data API
]
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",          # enable APIs, create SA + key
    "https://www.googleapis.com/auth/analytics.manage.users",  # share GA4 properties
]


def main():
    if not CLIENT.exists():
        sys.exit(f"ERROR: OAuth client not found at {CLIENT}")

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", open_browser=True,
                                  authorization_prompt_message="VISIT_THIS_URL: {url}")
    s = AuthorizedSession(creds)

    # 0) Enable the APIs this script needs (they were disabled -> 403 SERVICE_DISABLED).
    r = s.post(
        f"https://serviceusage.googleapis.com/v1/projects/{PROJECT_NUMBER}/services:batchEnable",
        json={"serviceIds": NEEDED_APIS})
    if r.status_code in (200, 201):
        print("enabling APIs:", ", ".join(NEEDED_APIS), "- waiting for propagation...")
        time.sleep(25)
    else:
        print(f"WARN batchEnable: {r.status_code} {r.text[:200]}")
        print("  If this 403s, enable the IAM API once here, wait 1 min, and re-run:")
        print("  https://console.cloud.google.com/apis/api/iam.googleapis.com/overview"
              f"?project={PROJECT_NUMBER}")
        time.sleep(10)

    # 1) Create the service account, retrying while the IAM API finishes propagating.
    created = False
    for attempt in range(6):
        r = s.post(
            f"https://iam.googleapis.com/v1/projects/{PROJECT_ID}/serviceAccounts",
            json={"accountId": SA_ACCOUNT_ID,
                  "serviceAccount": {"displayName": "GA4 read collector (marketing hub)"}})
        if r.status_code == 200:
            print("created service account:", SA_EMAIL)
            created = True
            break
        if r.status_code == 409:
            print("service account already exists:", SA_EMAIL)
            created = True
            break
        if r.status_code == 403 and "SERVICE_DISABLED" in r.text:
            print(f"  IAM API still propagating, retrying... ({attempt + 1}/6)")
            time.sleep(15)
            continue
        sys.exit(f"ERROR creating SA: {r.status_code} {r.text}")
    if not created:
        sys.exit("ERROR: IAM API did not become ready. Enable it once in the console, wait a "
                 "minute, and re-run:\n  https://console.cloud.google.com/apis/api/"
                 f"iam.googleapis.com/overview?project={PROJECT_NUMBER}")

    # 2) Create a key and write it to disk
    r = s.post(
        f"https://iam.googleapis.com/v1/projects/{PROJECT_ID}/serviceAccounts/{SA_EMAIL}/keys",
        json={"privateKeyType": "TYPE_GOOGLE_CREDENTIALS_FILE"})
    if r.status_code != 200:
        sys.exit(
            f"ERROR creating key: {r.status_code} {r.text}\n"
            "If key creation is disabled by an org policy, create it in the Console instead:\n"
            f"  IAM & Admin -> Service Accounts -> {SA_EMAIL} -> Keys -> Add key -> JSON\n"
            f"  and save the downloaded file as: {SA_KEY_OUT}")
    key_json = base64.b64decode(r.json()["privateKeyData"]).decode("utf-8")
    SA_KEY_OUT.write_text(key_json, encoding="utf-8")
    print("wrote key ->", SA_KEY_OUT)

    # 3) Grant the SA Viewer on each GA4 property (retry: a new SA can take a moment to exist)
    for pid, name in GA4_PROPERTIES.items():
        ok = False
        last = ""
        for _ in range(6):
            r = s.post(
                f"https://analyticsadmin.googleapis.com/v1beta/properties/{pid}/accessBindings",
                json={"user": SA_EMAIL, "roles": ["predefinedRoles/viewer"]})
            last = f"{r.status_code} {r.text[:160]}"
            if r.status_code in (200, 201):
                ok = True
                print(f"shared property {pid} ({name}) -> {SA_EMAIL}")
                break
            if r.status_code == 409 or "already exists" in r.text.lower():
                ok = True
                print(f"property {pid} ({name}) already shared")
                break
            time.sleep(5)
        if not ok:
            print(f"WARN could not share property {pid} ({name}): {last}\n"
                  f"  -> add {SA_EMAIL} as 'Viewer' in GA4 Admin -> Property Access Management.")

    print("\nDONE. The GA4 collector now uses the service-account key (no expiry).")
    print("Verify:  cd ..\\..\\Spam  &&  python lib\\collectors\\ga4.py sharpyard")


if __name__ == "__main__":
    main()
