"""finalize_hero_voice.py - render the chosen ElevenLabs hero voice WITH exact caption
timing, for the FutPicks WC video.

Calls the ElevenLabs /with-timestamps endpoint (returns audio + per-character alignment),
writes the hero voice mp3 AND a chunked SRT built from the exact alignment (so captions
land perfectly, unlike a Whisper guess). Overwrites the canonical voice_es.mp3/.srt the
video compose step reads.

  python finalize_hero_voice.py --voice-id <id> --text-file tuned.txt \
      --out-mp3 voice_es.mp3 --out-srt voice_es.srt \
      [--stability 0.55] [--style 0.1] [--max-chars 26]
"""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

import httpx

BASE = "https://api.elevenlabs.io"
ENV = Path(__file__).parent / ".env.elevenlabs"


def key() -> str:
    return ENV.read_text(encoding="utf-8").split("=", 1)[1].strip()


def _ts(s: float) -> str:
    if s < 0:
        s = 0
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        sec += 1; ms = 0
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def words_from_alignment(chars: list[str], starts: list[float], ends: list[float]) -> list[dict]:
    """Group per-character alignment into words with start/end times."""
    words: list[dict] = []
    cur = ""; w_start = None; w_end = None
    for c, st, en in zip(chars, starts, ends):
        if c.isspace():
            if cur:
                words.append({"w": cur, "t": w_start, "e": w_end}); cur = ""
            continue
        if not cur:
            w_start = st
        cur += c; w_end = en
    if cur:
        words.append({"w": cur, "t": w_start, "e": w_end})
    return words


def chunk_lines(words: list[dict], max_chars: int) -> list[dict]:
    cues: list[dict] = []; cur: list[dict] = []

    def flush():
        if cur:
            cues.append({"start": cur[0]["t"], "end": cur[-1]["e"],
                         "text": " ".join(w["w"] for w in cur)})
            cur.clear()

    for w in words:
        cand = " ".join(x["w"] for x in cur + [w])
        if len(cand) > max_chars and cur:
            flush()
        cur.append(w)
        if w["w"].rstrip().endswith((".", "?", "!", ":")) or len(cur) >= 5:
            flush()
    flush()
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice-id", required=True)
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--out-mp3", required=True)
    ap.add_argument("--out-srt", required=True)
    ap.add_argument("--model", default="eleven_v3")
    ap.add_argument("--stability", type=float, default=0.55)
    ap.add_argument("--style", type=float, default=0.1)
    ap.add_argument("--similarity", type=float, default=0.9)
    ap.add_argument("--max-chars", type=int, default=26)
    a = ap.parse_args()

    text = Path(a.text_file).read_text(encoding="utf-8").strip()
    body = {
        "text": text, "model_id": a.model,
        "voice_settings": {"stability": a.stability, "style": a.style,
                           "similarity_boost": a.similarity, "use_speaker_boost": True},
    }
    r = httpx.post(
        f"{BASE}/v1/text-to-speech/{a.voice_id}/with-timestamps",
        headers={"xi-api-key": key(), "Content-Type": "application/json"},
        params={"output_format": "mp3_44100_128"}, json=body, timeout=180,
    )
    if r.status_code != 200:
        sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:400]}")
    data = r.json()
    Path(a.out_mp3).write_bytes(base64.b64decode(data["audio_base64"]))

    al = data["alignment"]
    words = words_from_alignment(
        al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"])
    cues = chunk_lines(words, a.max_chars)
    with open(a.out_srt, "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{c['text']}\n\n")
    print(f"OK mp3={a.out_mp3}  srt={a.out_srt}  cues={len(cues)}  "
          f"dur={cues[-1]['end']:.1f}s  ~{len(text)} credits")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
