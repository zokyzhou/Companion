#!/usr/bin/env python3
"""Mindful Companion journal CLI — local-first, private emotional memory.

Single source of truth for reading, writing, and analyzing session entries.
Data lives under ~/.mindful-companion/ and never leaves this machine.

Subcommands:
  add       Append a session entry (from flags or --json stdin).
  list      Print recent entries (most recent first).
  context   Print a compact, agent-facing memory brief for the NEXT session:
            recent feelings, recurring triggers, and what has helped before.
  analyze   Print pattern stats (feeling counts, trigger counts, helped counts,
            rough trend of intensity over time).
  stats     One-line summary (entry count, span, streak).

Storage:
  ~/.mindful-companion/journal.jsonl   append-only, one JSON object per line
  ~/.mindful-companion/README.txt      privacy note (written on first use)

Design notes:
  - Append-only JSONL so a crash mid-write never corrupts prior entries.
  - No external dependencies (stdlib only) so it runs anywhere Python 3 exists.
  - Sensitive data: keep this directory out of file-sync / backups. See README.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(os.environ.get("MINDFUL_HOME", Path.home() / ".mindful-companion"))
JOURNAL = DATA_DIR / "journal.jsonl"
README = DATA_DIR / "README.txt"

PRIVACY_NOTE = """\
Mindful Companion — private local data
======================================
This folder holds your emotional check-in history. It is intended to stay on
THIS machine only.

- Do NOT sync this folder (Syncthing / cloud backup / git). It is personal.
- Entries are plain JSON lines in journal.jsonl.
- To wipe your history, delete journal.jsonl.
- This tool is a reflective companion, NOT a therapist or medical service.
"""


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        DATA_DIR.chmod(0o700)
    except OSError:
        pass
    if not README.exists():
        README.write_text(PRIVACY_NOTE)


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _read_entries() -> list[dict]:
    if not JOURNAL.exists():
        return []
    entries: list[dict] = []
    for line in JOURNAL.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            # Skip a single corrupt line rather than losing the whole journal.
            continue
    return entries


def _split_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    return [p.strip() for p in str(value).split(",") if p.strip()]


def cmd_add(args: argparse.Namespace) -> int:
    _ensure_dir()
    if args.json:
        raw = sys.stdin.read() if args.json == "-" else args.json
        payload = json.loads(raw)
    else:
        payload = {}
    entry = {
        "ts": payload.get("ts") or _now_iso(),
        "feeling": payload.get("feeling") or args.feeling or "",
        "intensity": payload.get("intensity", args.intensity),
        "triggers": payload.get("triggers") or _split_list(args.triggers),
        "helped": payload.get("helped") or _split_list(args.helped),
        "technique": payload.get("technique") or args.technique or "",
        "closing_feeling": payload.get("closing_feeling") or args.closing_feeling or "",
        "note": payload.get("note") or args.note or "",
    }
    with JOURNAL.open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"saved entry @ {entry['ts']} ({entry['feeling'] or 'unspecified'})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = _read_entries()
    if not entries:
        print("(no entries yet)")
        return 0
    recent = entries[-args.limit :][::-1]
    if args.json:
        print(json.dumps(recent, ensure_ascii=False, indent=2))
        return 0
    for e in recent:
        trig = ", ".join(e.get("triggers", [])) or "-"
        helped = ", ".join(e.get("helped", [])) or "-"
        print(
            f"{e.get('ts','?')}  {e.get('feeling','?')} "
            f"(int {e.get('intensity','?')})  "
            f"→ {e.get('closing_feeling','') or '?'}\n"
            f"    triggers: {trig}\n    helped: {helped}"
        )
    return 0


def _trend(intensities: list) -> str:
    nums = [i for i in intensities if isinstance(i, (int, float))]
    if len(nums) < 2:
        return "not enough data"
    first_half = nums[: len(nums) // 2]
    second_half = nums[len(nums) // 2 :]
    a = sum(first_half) / len(first_half)
    b = sum(second_half) / len(second_half)
    if b < a - 0.5:
        return f"easing (avg {a:.1f} → {b:.1f})"
    if b > a + 0.5:
        return f"intensifying (avg {a:.1f} → {b:.1f})"
    return f"steady (avg ~{b:.1f})"


def cmd_analyze(args: argparse.Namespace) -> int:
    entries = _read_entries()
    if not entries:
        print("(no entries yet — nothing to analyze)")
        return 0
    feelings = Counter(e.get("feeling", "").lower() for e in entries if e.get("feeling"))
    triggers = Counter(
        t.lower() for e in entries for t in e.get("triggers", []) if t
    )
    helped = Counter(h.lower() for e in entries for h in e.get("helped", []) if h)
    intensities = [e.get("intensity") for e in entries]

    out = {
        "entries": len(entries),
        "top_feelings": feelings.most_common(5),
        "recurring_triggers": triggers.most_common(5),
        "what_helped_most": helped.most_common(5),
        "intensity_trend": _trend(intensities),
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print(f"entries: {out['entries']}")
    print(f"intensity trend: {out['intensity_trend']}")
    print("top feelings: " + (", ".join(f"{k} x{v}" for k, v in out["top_feelings"]) or "-"))
    print("recurring triggers: " + (", ".join(f"{k} x{v}" for k, v in out["recurring_triggers"]) or "-"))
    print("what helped most: " + (", ".join(f"{k} x{v}" for k, v in out["what_helped_most"]) or "-"))
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    """Compact memory brief the agent reads at the START of a new session."""
    entries = _read_entries()
    if not entries:
        print("MEMORY: first session — no history yet. Start warm and open.")
        return 0
    recent = entries[-args.limit :]
    triggers = Counter(t.lower() for e in entries for t in e.get("triggers", []) if t)
    helped = Counter(h.lower() for e in entries for h in e.get("helped", []) if h)
    last = entries[-1]
    lines = ["MEMORY BRIEF (private, local-only):"]
    lines.append(f"- history: {len(entries)} check-ins on record")
    lines.append(f"- last check-in: {last.get('ts','?')} — felt '{last.get('feeling','?')}', left '{last.get('closing_feeling','') or 'better'}'")
    if triggers:
        lines.append("- recurring triggers: " + ", ".join(f"{k}" for k, _ in triggers.most_common(3)))
    if helped:
        lines.append("- what's helped before: " + ", ".join(f"{k}" for k, _ in helped.most_common(3)))
    recent_feelings = [e.get("feeling", "?") for e in recent]
    lines.append("- recent feelings: " + ", ".join(recent_feelings))
    lines.append("Use gently — reference patterns as offers, not diagnoses. Do not assume; ask.")
    print("\n".join(lines))
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    entries = _read_entries()
    if not entries:
        print("0 entries")
        return 0
    first = entries[0].get("ts", "?")
    last = entries[-1].get("ts", "?")
    print(f"{len(entries)} entries — first {first}, last {last}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Mindful Companion journal (local, private).")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="append a session entry")
    a.add_argument("--feeling")
    a.add_argument("--intensity", type=int, help="0-10")
    a.add_argument("--triggers", help="comma-separated")
    a.add_argument("--helped", help="comma-separated techniques/things that helped")
    a.add_argument("--technique", help="primary technique used")
    a.add_argument("--closing-feeling", dest="closing_feeling")
    a.add_argument("--note")
    a.add_argument("--json", help="JSON object, or '-' to read from stdin")
    a.set_defaults(func=cmd_add)

    l = sub.add_parser("list", help="print recent entries")
    l.add_argument("--limit", type=int, default=10)
    l.add_argument("--json", action="store_true")
    l.set_defaults(func=cmd_list)

    c = sub.add_parser("context", help="compact memory brief for next session")
    c.add_argument("--limit", type=int, default=5)
    c.set_defaults(func=cmd_context)

    an = sub.add_parser("analyze", help="pattern stats across all entries")
    an.add_argument("--json", action="store_true")
    an.set_defaults(func=cmd_analyze)

    s = sub.add_parser("stats", help="one-line summary")
    s.set_defaults(func=cmd_stats)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
