"""Upload a vertical MP4 to YouTube as a Short.

A Short is just a vertical (<= 60s, 9:16) video with #Shorts in the title or
description; there is no special upload audit gate. We append #Shorts once,
strip em-dashes, run the title/description through the hub operator lint, then
videos.insert with snippet/status. On success we print the watch URL and log the
run to the hub.

Auth (mirrors ga_admin.py): user OAuth token at seo/.youtube-token.json, client
secret at seo/youtube-oauth-client.json (NEVER in the hub; both gitignored).

Usage:
  python youtube_shorts_upload.py --file tip.mp4 --title "Prop of the night" \
      --description "Usage + minutes edge. Full slate at nbaproplab.com" \
      [--tags nba,props] [--privacy public|unlisted|private] [--account <channel>] [--dry-run]

The pure body builder build_video_body() is duplicated here AND mirrored in the
hub as lib/youtube_body.py so it is unit-testable without the google libs.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Reuse the hub's operator lint + run log (single source of truth).
_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # type: ignore
except Exception:
    guardrails = None

HERE = Path(__file__).parent
OAUTH_TOKEN = HERE / ".youtube-token.json"
CLIENT_SECRET = HERE / "youtube-oauth-client.json"
UPLOAD_LOG = HERE / "youtube_upload_log.jsonl"
RECORD_RUN = _HUB_LIB / "record_run.py"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def build_video_body(title, description="", tags=None, privacy="unlisted"):
    """Pure: build the videos.insert body. Mirrored in hub lib/youtube_body.py."""
    def clean(s):
        return (s or "").replace("—", " - ").replace("–", "-")
    title = clean(title)
    if "#Shorts" not in title:
        title = f"{title} #Shorts"
    return {
        "snippet": {"title": title[:100], "description": clean(description), "tags": tags or []},
        "status": {"privacyStatus": privacy if privacy in ("public", "unlisted", "private") else "unlisted"},
    }


def _youtube_client():
    """Build an authenticated YouTube Data API v3 client (user OAuth)."""
    from google.oauth2.credentials import Credentials as UserCredentials
    import google.auth.transport.requests as _gtr
    from googleapiclient.discovery import build

    if not OAUTH_TOKEN.exists():
        if not CLIENT_SECRET.exists():
            sys.exit(
                f"ERROR: no YouTube credentials. Place an OAuth client at "
                f"{CLIENT_SECRET.name} and run an OAuth flow to create {OAUTH_TOKEN.name}."
            )
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
        creds = flow.run_local_server(port=0)
        OAUTH_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    else:
        creds = UserCredentials.from_authorized_user_file(str(OAUTH_TOKEN), SCOPES)
        if not creds.valid and creds.refresh_token:
            creds.refresh(_gtr.Request())
            OAUTH_TOKEN.write_text(creds.to_json(), encoding="utf-8")
    return build("youtube", "v3", credentials=creds)


def _log_upload(entry):
    with UPLOAD_LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _record_run(url):
    """Best-effort hub run log; never blocks the upload result."""
    if not RECORD_RUN.exists():
        return
    try:
        subprocess.run(
            [sys.executable, str(RECORD_RUN),
             "--routine", "youtube-short",
             "--category", "youtube",
             "--link", f"watch|{url}"],
            check=False,
        )
    except Exception:
        pass


def upload_short(file, title, description="", tags=None, privacy="unlisted",
                 account=None, dry_run=False):
    """Resilient live upload. Returns a result dict; never raises."""
    body = build_video_body(title, description, tags, privacy)

    # Operator lint on the (cleaned) caption text before anything leaves the box.
    lint_target = f"{body['snippet']['title']}\n{body['snippet']['description']}"
    if guardrails is not None:
        violations = guardrails.lint_text(lint_target)
        if violations:
            return {"ok": False, "error": "blocked by guardrails", "violations": violations}

    if dry_run:
        return {"ok": True, "dry_run": True, "body": body, "account": account}

    try:
        from googleapiclient.http import MediaFileUpload
        path = Path(file)
        if not path.exists():
            return {"ok": False, "error": f"file not found: {file}"}
        yt = _youtube_client()
        media = MediaFileUpload(str(path), chunksize=-1, resumable=True,
                                mimetype="video/*")
        request = yt.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response.get("id")
        url = f"https://www.youtube.com/watch?v={video_id}"
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "video_id": video_id,
            "url": url,
            "title": body["snippet"]["title"],
            "privacy": body["status"]["privacyStatus"],
            "account": account,
            "file": str(path),
        }
        _log_upload(entry)
        _record_run(url)
        return {"ok": True, "video_id": video_id, "url": url}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Upload a vertical MP4 to YouTube as a Short.")
    ap.add_argument("--file", required=True, help="path to the vertical mp4")
    ap.add_argument("--title", required=True, help="video title (#Shorts appended)")
    ap.add_argument("--description", default="", help="video description")
    ap.add_argument("--tags", default="", help="comma-separated tags")
    ap.add_argument("--privacy", default="unlisted",
                    choices=["public", "unlisted", "private"])
    ap.add_argument("--account", default=None, help="channel label (for the log)")
    ap.add_argument("--dry-run", action="store_true",
                    help="build + lint the body, do not upload")
    args = ap.parse_args(argv)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] or None
    result = upload_short(
        file=args.file, title=args.title, description=args.description,
        tags=tags, privacy=args.privacy, account=args.account, dry_run=args.dry_run,
    )
    if result.get("ok") and result.get("url"):
        print(result["url"])
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
