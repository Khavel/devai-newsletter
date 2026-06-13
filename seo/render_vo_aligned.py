"""render_vo_aligned.py - ElevenLabs hero VO + EXACT alignment for a multi-shot edit.

Outputs (next to --out-mp3): the mp3, a chunked caption SRT, and sentences.json
(list of {text, start, end} per sentence) so the video generator can time each shot
to a sentence boundary. Same voice/settings as finalize_hero_voice (Roque v3).

  python render_vo_aligned.py --voice-id <id> --text-file guion.txt \
      --out-mp3 vo.mp3 --out-srt vo.srt --out-sentences sentences.json
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
from pathlib import Path

import httpx

BASE = "https://api.elevenlabs.io"
ENV = Path(__file__).parent / ".env.elevenlabs"


def key() -> str:
    return ENV.read_text(encoding="utf-8").split("=", 1)[1].strip()


def _ts(s: float) -> str:
    s = max(0.0, s)
    h = int(s // 3600); m = int((s % 3600) // 60); sec = int(s % 60)
    ms = int(round((s - int(s)) * 1000))
    if ms == 1000:
        sec += 1; ms = 0
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def words_from_alignment(chars, starts, ends):
    words = []; cur = ""; ws = we = None
    for c, st, en in zip(chars, starts, ends):
        if c.isspace():
            if cur:
                words.append({"w": cur, "t": ws, "e": we}); cur = ""
            continue
        if not cur:
            ws = st
        cur += c; we = en
    if cur:
        words.append({"w": cur, "t": ws, "e": we})
    return words


def chunk_lines(words, max_chars):
    cues = []; cur = []

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


def sentences_from_chars(chars, starts, ends):
    """Split into sentences on . ? ! and record each sentence's start/end time."""
    out = []; buf = ""; s_start = None; last_end = None; started = False
    for c, st, en in zip(chars, starts, ends):
        if not c.isspace() and not started:
            s_start = st; started = True
        buf += c; last_end = en
        if c in ".?!":
            text = buf.strip()
            if text:
                out.append({"text": text, "start": s_start, "end": last_end})
            buf = ""; started = False
    if buf.strip():
        out.append({"text": buf.strip(), "start": s_start or 0.0, "end": last_end or 0.0})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice-id", required=True)
    ap.add_argument("--text-file", required=True)
    ap.add_argument("--out-mp3", required=True)
    ap.add_argument("--out-srt", required=True)
    ap.add_argument("--out-sentences", required=True)
    ap.add_argument("--model", default="eleven_v3")
    ap.add_argument("--stability", type=float, default=0.55)
    ap.add_argument("--style", type=float, default=0.1)
    ap.add_argument("--similarity", type=float, default=0.9)
    ap.add_argument("--max-chars", type=int, default=26)
    a = ap.parse_args()

    text = Path(a.text_file).read_text(encoding="utf-8").strip()
    body = {"text": text, "model_id": a.model,
            "voice_settings": {"stability": a.stability, "style": a.style,
                               "similarity_boost": a.similarity, "use_speaker_boost": True}}
    r = httpx.post(f"{BASE}/v1/text-to-speech/{a.voice_id}/with-timestamps",
                   headers={"xi-api-key": key(), "Content-Type": "application/json"},
                   params={"output_format": "mp3_44100_128"}, json=body, timeout=180)
    if r.status_code != 200:
        sys.exit(f"ElevenLabs error {r.status_code}: {r.text[:400]}")
    data = r.json()
    Path(a.out_mp3).write_bytes(base64.b64decode(data["audio_base64"]))
    al = data["alignment"]
    ch, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]

    cues = chunk_lines(words_from_alignment(ch, st, en), a.max_chars)
    with open(a.out_srt, "w", encoding="utf-8") as f:
        for i, c in enumerate(cues, 1):
            f.write(f"{i}\n{_ts(c['start'])} --> {_ts(c['end'])}\n{c['text']}\n\n")

    sents = sentences_from_chars(ch, st, en)
    Path(a.out_sentences).write_text(json.dumps(sents, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK mp3={a.out_mp3}  cues={len(cues)}  sentences={len(sents)}  dur={en[-1]:.1f}s  ~{len(text)} cred")
    for i, s in enumerate(sents):
        print(f"  S{i}: {s['start']:.2f}-{s['end']:.2f}  {s['text']}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
