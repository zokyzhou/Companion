# Mindful Companion

A warm, voice-first reflective companion skill for the Openbase agent. You say
how you're feeling; it guides a natural spoken conversation to help you
understand *why* and leave feeling a little better — drawing on mindfulness/CBT
techniques and a private, local-only memory that personalizes over time.

**Not a therapist, doctor, or crisis service.** See `references/safety.md`.

## Layout
- `SKILL.md` — trigger, the conversational flow, memory hooks, boundaries.
- `references/techniques.md` — spoken technique scripts (grounding, breathing,
  reframing, reflective listening, gratitude, naming, self-compassion).
- `references/safety.md` — crisis signals + gentle deferral to real help.
- `scripts/journal.py` — local private memory CLI (stdlib only, no deps).

## Memory CLI
```bash
python3 scripts/journal.py context     # memory brief for the next session
python3 scripts/journal.py add ...      # append a session entry
python3 scripts/journal.py analyze      # patterns: triggers, what helped, trend
python3 scripts/journal.py list         # recent entries
```

## Privacy
Data lives in `~/.mindful-companion/` (override with `MINDFUL_HOME`). It is
local-only. **Do not sync or back up this folder.** Delete `journal.jsonl` to
wipe your history.
