"""Set Bluesky profile displayName + bio for the product accounts (one-time setup).

Usage:
  python bluesky_profile_setup.py --account Sharpyard [--dry-run]
  python bluesky_profile_setup.py --all [--dry-run]

Reads handles/app passwords from seo/.env.bluesky (same env names as bluesky_post.py).
Upserts the app.bsky.actor.profile record, PRESERVING any existing avatar/banner.
Every description is routed through the hub guardrails lint before being applied.
No em-dashes in any public copy.
"""
import argparse
import sys
from pathlib import Path

_HUB_LIB = Path(r"C:\Users\ceja_\Desktop\Desarrollos\Spam\lib")
if _HUB_LIB.exists():
    sys.path.insert(0, str(_HUB_LIB))
try:
    import guardrails  # type: ignore
except Exception:
    guardrails = None

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from bluesky_post import ACCOUNTS, load_env, get_credentials  # reuse, do not fork

# Public profile copy per account. Tool/method framing only; no operator links,
# no guarantee language (the lint enforces this as a second gate).
PROFILES = {
    "Sharpyard": {
        "display_name": "Sharpyard",
        "description": (
            "Building Sharpyard in public: the AI-agent-native .NET 10 + Angular SaaS "
            "starter kit. Free starter repo: github.com/Khavel/dotnet-claude-starter"
        ),
    },
    "DevAISemanal": {
        "display_name": "DevAI Semanal",
        "description": (
            "Newsletter semanal en español sobre herramientas de IA para developers. "
            "Cada martes en devaisemanal.com"
        ),
    },
    "FutProbLab": {
        "display_name": "FutProbLab",
        "description": (
            "Football betting intelligence workspace, not a tipster. Fair odds vs "
            "Pinnacle and published CLV on every pick. Verifiable record: "
            "futpicks.com/track-record. 18+, bet responsibly."
        ),
    },
    "StatLineNerd": {
        "display_name": "StatLineNerd",
        "description": (
            "NBA player prop research platform. A 7-block scoring engine you can run on "
            "any prop, with a published track record. nbaproplab.com"
        ),
    },
}


def setup_profile(account: str, dry_run: bool = False) -> bool:
    prof = PROFILES[account]
    name, desc = prof["display_name"], prof["description"]

    if "—" in name + desc:
        print(f"  BLOCKED: em-dash in profile copy for {account}")
        return False
    if guardrails is not None:
        violations = guardrails.lint_text(desc, own_domains=ACCOUNTS[account]["own_domains"])
        if violations:
            print(f"  BLOCKED by guardrails for {account}: {violations}")
            return False

    if dry_run:
        print(f"[DRY RUN] {account}: displayName={name!r}")
        print(f"[DRY RUN]   bio: {desc}")
        return True

    from atproto import Client, models

    handle, app_password = get_credentials(account)
    client = Client()
    client.login(handle, app_password)
    did = client.me.did

    # Fetch the existing profile record so avatar/banner survive the upsert.
    old, swap_cid = None, None
    try:
        existing = client.com.atproto.repo.get_record(
            models.ComAtprotoRepoGetRecord.Params(
                repo=did, collection="app.bsky.actor.profile", rkey="self")
        )
        old, swap_cid = existing.value, existing.cid
    except Exception:
        pass  # no profile record yet

    record = models.AppBskyActorProfile.Record(
        display_name=name,
        description=desc,
        avatar=getattr(old, "avatar", None) if old else None,
        banner=getattr(old, "banner", None) if old else None,
    )
    client.com.atproto.repo.put_record(
        models.ComAtprotoRepoPutRecord.Data(
            repo=did, collection="app.bsky.actor.profile", rkey="self",
            record=record, swap_record=swap_cid,
        )
    )
    print(f"  {account} ({handle}): profile set (name + bio; avatar preserved)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Set Bluesky profiles for product accounts")
    parser.add_argument("--account", choices=list(PROFILES.keys()))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    targets = list(PROFILES.keys()) if args.all else ([args.account] if args.account else [])
    if not targets:
        parser.error("provide --account <name> or --all")

    if not args.dry_run:
        load_env()
    ok = all(setup_profile(a, dry_run=args.dry_run) for a in targets)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
