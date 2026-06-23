"""elevenlabs_tts.py - ElevenLabs voiceover runner (HERO renders only; hybrid plan).

The hybrid workflow: iterate the script + timing + pacing for FREE in edge-tts
(lib/tts_stitch.py / edge_tts_captions.py), then send ONLY the near-final script
here for 2-3 polish renders on the human voice. This keeps the ElevenLabs credit
burn low enough to live on the $5 Starter tier.

Key is read from seo/.env.elevenlabs (line `ELEVENLABS_API_KEY=...`) or the env var
ELEVENLABS_API_KEY. The .env.* files are gitignored (never committed).

Usage:
  python elevenlabs_tts.py voices --es              # list Spanish-relevant voices
  python elevenlabs_tts.py say --voice-id <id> --text-file v.txt --out out.mp3 \
      [--model eleven_multilingual_v2] [--stability 0.45] [--style 0.15]

NOTE on cost: every `say` call consumes credits (1 credit/char). Lock the wording
BEFORE generating; do not loop this in a tuning cycle (that is what edge-tts is for).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

BASE = "https://api.elevenlabs.io"
ENV_FILE = Path(__file__).parent / ".env.elevenlabs"


def load_key() -> str:
    import os
    if os.environ.get("ELEVENLABS_API_KEY"):
        return os.environ["ELEVENLABS_API_KEY"].strip()
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("ELEVENLABS_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
            if "=" not in line and len(line) > 20:  # a bare key on its own line
                return line
    sys.exit(
        f"No API key. Put `ELEVENLABS_API_KEY=...` in {ENV_FILE} "
        "or set the ELEVENLABS_API_KEY env var."
    )


def cmd_voices(args):
    key = load_key()
    r = httpx.get(f"{BASE}/v1/voices", headers={"xi-api-key": key}, timeout=30)
    r.raise_for_status()
    voices = r.json().get("voices", [])
    rows = []
    for v in voices:
        labels = v.get("labels") or {}
        lang = (labels.get("language") or "").lower()
        accent = (labels.get("accent") or "").lower()
        is_es = "spanish" in lang or "es" == lang or any(
            a in accent for a in ("spanish", "castilian", "latin", "mexican", "argent")
        ) or "spanish" in (v.get("name", "").lower())
        if args.es and not is_es:
            continue
        rows.append((v.get("name", "?"), v.get("voice_id", "?"),
                     labels.get("accent", ""), labels.get("description", ""),
                     labels.get("gender", "")))
    print(f"{'NAME':<22} {'VOICE_ID':<24} {'ACCENT':<14} {'GENDER':<8} DESC")
    print("-" * 90)
    for name, vid, accent, desc, gender in rows:
        print(f"{name:<22} {vid:<24} {accent:<14} {gender:<8} {desc}")
    print(f"\n{len(rows)} voices" + (" (Spanish-filtered)" if args.es else ""))


def cmd_say(args):
    key = load_key()
    text = args.text if args.text else Path(args.text_file).read_text(encoding="utf-8").strip()
    settings = {
        "stability": args.stability,
        "similarity_boost": args.similarity,
        "style": args.style,
        "use_speaker_boost": True,
        "speed": args.speed,  # 0.7-1.2 (1.0 = unchanged). >1 = faster/less "slow"; works on all models incl. v3.
    }
    body = {"text": text, "model_id": args.model, "voice_settings": settings}
    url = f"{BASE}/v1/text-to-speech/{args.voice_id}"
    r = httpx.post(
        url, headers={"xi-api-key": key, "Content-Type": "application/json"},
        params={"output_format": args.output_format}, json=body, timeout=120,
    )
    if r.status_code != 200:
        sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:500]}")
    Path(args.out).write_bytes(r.content)
    chars = len(text)
    print(f"OK {args.out}  ({len(r.content)//1024} KB)  ~{chars} credits  model={args.model}")


def main():
    ap = argparse.ArgumentParser(description="ElevenLabs voiceover (hero renders)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("voices", help="list voices")
    pv.add_argument("--es", action="store_true", help="only Spanish-relevant voices")
    pv.set_defaults(func=cmd_voices)

    ps = sub.add_parser("say", help="synthesize text to mp3")
    ps.add_argument("--voice-id", required=True)
    ps.add_argument("--text-file")
    ps.add_argument("--text")
    ps.add_argument("--out", required=True)
    ps.add_argument("--model", default="eleven_multilingual_v2",
                    help="eleven_multilingual_v2 (reliable) or eleven_v3 (most human, audio tags)")
    ps.add_argument("--stability", type=float, default=0.45)
    ps.add_argument("--similarity", type=float, default=0.8)
    ps.add_argument("--style", type=float, default=0.1)
    ps.add_argument("--speed", type=float, default=1.0, help="0.7-1.2; >1 speeds up (less 'slow/robotic')")
    ps.add_argument("--output-format", default="mp3_44100_128")
    ps.set_defaults(func=cmd_say)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
