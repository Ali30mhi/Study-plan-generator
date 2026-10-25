# Study Plan Generator

Turns your courses into a realistic, day-by-day study schedule with clock
times — and exports it straight to your calendar.

## Features

- **Timed sessions** — each day is split into focus sessions with breaks
  (Pomodoro-style, 50 + 10 minutes by default)
- **Fair split** — study time is shared between courses in proportion to
  their units, and courses alternate through the day
- **Exam-aware** — in the last 14 days before an exam that course gets up
  to 3x more time; after the exam it leaves the plan
- **Rest days** — Friday by default, or any days you choose
- **Three outputs**
  - `study_plan.txt` — readable schedule
  - `study_plan.csv` — open in Excel or Google Sheets
  - `study_plan.ics` — import into Google Calendar, Outlook or Apple Calendar
    (exam days included)
- Friendly input: press Enter for defaults, invalid answers are asked again
- Pure Python, no dependencies (Python 3.8+)

## Run

```bash
python3 plan-generator.py
```

## Example

Two courses — `math` (3 units) and `physics` (2 units, exam on 2026-11-10),
4 hours a day, Fridays off:

```
Plan:   2026-10-25 to 2026-11-23  (26 study days, rest: Friday)
Daily:  4 x 50 min focus with 10 min breaks, starting 09:00
Total:  86h 40m of focused study

  math       60h 50m  ████████████████████████
  physics    25h 50m  ██████████                 exam 2026-11-10

Sunday 2026-10-25
------------------------------
  09:00-09:50  math
  10:00-10:50  physics
  11:00-11:50  math
  12:00-12:50  physics
```

## Add it to Google Calendar

1. Open Google Calendar on a computer
2. Settings → **Import & export** → **Import**
3. Choose `study_plan.ics` and the calendar to add it to

Tip: create a separate calendar (e.g. "Study") first, so you can hide or
delete the whole plan in one click.

## How it works

Each study day gets `(hours × 60 + break) ÷ (session + break)` sessions.
Sessions are handed out with a smooth weighted round-robin: every course
collects "credit" equal to its weight, the course with the most credit gets
the next session, and its credit drops by the total weight. This keeps the
long-run split proportional to units while mixing courses within each day.
A course's weight is its units, ramped up to 3x as its exam approaches.
