---
openbase_report:
  thread_id: s_e2790be856d54633af0acd703cddd7f8
  thread_name: mindfulness-companion-skill
  agent_name: Joanie
---

# Mindful Companion — Design Doc + Skeleton

Status: v1 skeleton shipped and tested. A voice-first reflective companion skill
on top of the Openbase agent. The user expresses a feeling; the skill guides a
natural spoken conversation to help them understand *why* and leave feeling a
little better; a local-first, private memory personalizes over time.

> **Not a therapist, doctor, or crisis service.** See §7 Safety.

Delivered artifacts:
- Skill package: `~/.agents/skills/mindful-companion/`
  - `SKILL.md`, `references/techniques.md`, `references/safety.md`
  - `scripts/journal.py` (local private memory CLI), `README.md`
- Private data dir: `~/.mindful-companion/` (git-ignored by nature, never synced)

## 1. Product concept
A warm companion you talk to out loud when you're feeling something and want to
work through it. It is **conversational, not a questionnaire** — it responds to
what you actually said, keeps its turns short, and lets you lead the pace. Over
time it quietly remembers your emotional history (locally, privately) so it can
personalize: recall what's triggered you, what's helped, and whether things are
easing.

**Defining stance — an ANTI-SOLUTION tool.** The companion deliberately does
*not* give advice, fixes, tips, or action plans, and does *not* rush to reassure.
Its entire purpose is to facilitate the user's own **self-discovery** through
open, curious, reflective questions. It mostly reflects, mirrors, and asks —
resisting the urge to advise or problem-solve — so insight arrives from the
*user*, not the agent. People usually still leave lighter, but from being deeply
heard and understanding themselves, not from being cheered up or handed answers.

Persona: sounds like a warm, intelligent, endlessly curious friend (Mel Robbins
energy) who is always in your corner — never a neutral assistant.

Design pillars:
- **Anti-solution, pro-self-discovery.** Questions, not answers. The agent is a
  mirror and guide, not an answer machine.
- **Heard first, never "fixed."** Reflective listening is the whole posture; no
  premature reassurance or silver linings.
- **Personal, not cold-start.** Memory brief loaded at the top of each session.
- **Private by construction.** Sensitive data stays on-device only.
- **Safe by default.** Clear boundaries + gentle deferral to real help.

## 2. Conversation flow (a flexible arc, not a script)
The agent moves through phases as a gentle arc, looping back as needed. The
overriding rule: **respond to what they said before moving on; one question per
turn; short turns; user sets the pace.** The user talks ~70%, the agent ~30%.

1. **Express** — open the door, let the feeling out, don't rush.
2. **Clarify / name** — attach a precise word ("name it to tame it"); optional
   intensity 0–10 for tracking.
3. **Explore why** — Socratic, gentle search for trigger + the thought beneath
   the feeling. This is where most time is spent. Reflect, don't interrogate.
4. **Deepen toward their own insight** — stay in open, reflective questions;
   invite any perspective shift *from them* ("what do you make of that?"), never
   deliver it. Grounding/breathing offered *only* if too activated to reflect —
   a way back into exploration, not a fix.
5. **Close on their insight** — let *them* name what shifted and what they're
   taking away; reflect it back without adding a moral or pep talk. End warmly.

Loop back any time new emotion surfaces. Skipping/reordering is allowed — the
user leads. Anti-solution stance holds throughout: reflect and ask, don't solve.

## 3. Techniques library
Encoded in `references/techniques.md` with spoken scripts and a "match technique
to state" guide. Included: naming/labeling, reflective listening, 5-4-3-2-1
grounding, breathing (long-exhale/box), CBT cognitive reframing, gratitude/
savoring, and a self-compassion break. Rules: one technique per session, ask
permission, pause and wait, drop it warmly if it isn't landing.

## 4. Memory model (local-first, private)
**What's stored** per session entry (append-only JSONL):
`ts, feeling, intensity (0–10), triggers[], helped[], technique, closing_feeling,
note`.

**Where:** `~/.mindful-companion/journal.jsonl` (overridable via `MINDFUL_HOME`).
Dir created `0700`; a `README.txt` privacy note is written on first use. Append-
only so a crash mid-write never corrupts prior entries; a single corrupt line is
skipped, not fatal.

**How it's analyzed** — one CLI, single source of truth (`scripts/journal.py`):
- `context` → compact **memory brief** the agent reads at the *start* of a
  session (recent feelings, recurring triggers, what's helped, last close). Used
  as gentle *offers*, never diagnosis.
- `analyze` → pattern stats across all entries: top feelings, recurring
  triggers, what helped most, and an intensity **trend** (easing / steady /
  intensifying).
- `add` → append an entry (flags or `--json`). `list` / `stats` for review.

This gives both cadences requested: inline personalization every session
(`context`) and a deeper pattern pass on demand (`analyze`).

## 5. Skill packaging (Openbase skill in ~/.agents/skills)
```
~/.agents/skills/mindful-companion/
  SKILL.md                  name/description/trigger + the conversational flow
  references/
    techniques.md           technique library (spoken scripts)
    safety.md               crisis signals + gentle deferral (read first)
  scripts/
    journal.py              stdlib-only, no deps; local private memory CLI
  README.md
```
`SKILL.md` front matter drives discovery: triggers on the user voicing a
feeling, distress, or asking for a check-in / to vent / calm down. The flow,
memory hooks (`context` at start, `add` at end, `analyze` on demand), and
boundaries live in the instructions. No external dependencies — runs anywhere
Python 3 exists.

## 6. Voice UX
- **Short turns.** One or two sentences; never stack questions.
- **Reflect before advancing.** Mirror their words first.
- **Match energy.** Softer and slower when they're low; never chipper at pain.
- **Ask permission** before any exercise.
- **Silent memory ops.** Never narrate CLI commands or read raw data / paths
  aloud.
- **Pacing exercises for voice.** Breathing/grounding are spoken slowly with
  real pauses, counting *with* the user.
- **Graceful close.** Always leave the door open ("I'm around whenever").

## 7. Safety design (important)
Encoded in `references/safety.md`, flagged in `SKILL.md` as **read first, keep
active, overrides everything**.
- **Boundary:** explicitly not a therapist/doctor/crisis line; no diagnosis, no
  medical/medication advice; warmly points to real human help.
- **Crisis signals watched:** suicidal ideation/plan/means, intent to harm
  others, abuse/immediate danger, medical emergency/psychosis, self-harm-linked
  substance use.
- **Response (gentle deferral, not a robotic wall):** stay warm → name the limit
  → offer concrete help (US defaults **911**, **988**, Crisis Text Line **741741**;
  adapt to region) → encourage a real human connection now → ask about immediate
  safety → never argue/diagnose/talk them out of it.
- **Privacy as safety:** local-only, never read entries aloud, keep out of sync/
  backup.
- **Tone rules:** no toxic positivity, no shame, never rush someone off; when in
  doubt, listen more and defer sooner.

## 8. Assumptions & defaults (confirmed / chosen)
- Single user (Zoky); memory keyed to one journal file. Multi-user would key by
  a profile arg — deferred.
- Storage: local, git-ignored, `0700`; plaintext JSONL for v1. **Encryption at
  rest is a documented next step**, not in v1 (kept simple + dependency-free).
- Region for crisis resources: **US (988/911/741741)** by default; adapt if the
  user's region is known.
- Sessions are **user-initiated** for v1; scheduled proactive check-ins are a
  future option (could use routines/cron).
- Memory analysis: both inline (`context`) and on-demand (`analyze`).

## 9. Roadmap / next steps
- **Encryption at rest** (OS keychain passphrase) for the journal.
- **Explicit sync-exclusion** wiring (ensure `~/.mindful-companion/` is ignored
  by Syncthing/backups) beyond the README note.
- **Scheduled gentle check-ins** via routines ("want to talk today?").
- **Richer trend analysis** (time-of-day/day-of-week patterns, trigger→technique
  effectiveness).
- **Region auto-detect** for crisis resources.
- **Multi-user profiles** if others use the same agent.
- Optional: package via boilersync `skills.sh` template for shareability.

## 10. Try it
```bash
python3 ~/.agents/skills/mindful-companion/scripts/journal.py context
python3 ~/.agents/skills/mindful-companion/scripts/journal.py add \
  --feeling anxious --intensity 7 --triggers "deadline" --helped breathing \
  --closing-feeling calmer
python3 ~/.agents/skills/mindful-companion/scripts/journal.py analyze
```
Then just talk to the agent: *"I'm feeling really overwhelmed."*
