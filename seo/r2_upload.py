"""Upload a local file to the marketing R2 bucket and print its permanent public URL.

Reads R2 creds from seo/.env.r2 (gitignored). The Metricool posting routines need this
because Metricool fetches media by URL (and silently drops expiring/private links), so a
video must live at a permanent public URL before it can be posted.

Usage:
  python r2_upload.py <local_path> [<r2_key>]
  # prints the public URL on success (and nothing else, so it can be captured in a var)
"""
import mimetypes
import sys
from pathlib import Path

ENV = Path(__file__).parent / ".env.r2"


def load_env():
    cfg = {}
    if not ENV.exists():
        sys.exit("ERROR: seo/.env.r2 not found")
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python r2_upload.py <local_path> [<r2_key>]")
    local = Path(sys.argv[1])
    if not local.exists():
        sys.exit(f"ERROR: file not found: {local}")
    cfg = load_env()
    key = sys.argv[2] if len(sys.argv) > 2 else local.name
    try:
        import boto3
    except ImportError:
        sys.exit("ERROR: boto3 not installed. Run: pip install boto3")
    s3 = boto3.client(
        "s3",
        endpoint_url=cfg["R2_ENDPOINT"],
        aws_access_key_id=cfg["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=cfg["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
    )
    ctype = mimetypes.guess_type(str(local))[0] or "application/octet-stream"
    s3.upload_file(str(local), cfg["R2_BUCKET"], key, ExtraArgs={"ContentType": ctype})
    print(cfg["R2_PUBLIC_BASE"].rstrip("/") + "/" + key)


if __name__ == "__main__":
    main()
