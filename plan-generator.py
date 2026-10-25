#!/usr/bin/env python3
"""
Study Plan Generator

Builds a day-by-day study schedule from your courses, their units and
(optionally) their exam dates. Each day is split into focus sessions with
short breaks, Pomodoro-style. Time is shared between courses in proportion
to their units, courses are interleaved through the day, a course gets
extra time as its exam gets close, and it leaves the plan after the exam.

Output files:
  study_plan.txt  readable schedule with clock times
  study_plan.csv  for Excel / Google Sheets
  study_plan.ics  import into Google Calendar, Outlook or Apple Calendar
"""

import csv
import datetime as dt
import uuid
from dataclasses import dataclass, field
from typing import Optional

WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
EXAM_BOOST_DAYS = 14   # start giving a course extra time this many days before its exam
EXAM_BOOST_MAX = 2.0   # extra weight on the last day before the exam (3x the normal share)


@dataclass
class Course:
    name: str
    units: int
    exam: Optional[dt.date] = None


@dataclass
class Settings:
    start_date: dt.date
    days: int
    hours_per_day: float
    day_start: dt.time
    session_min: int = 50
    break_min: int = 10
    rest_days: set = field(default_factory=set)   # 0 = Monday ... 6 = Sunday


@dataclass
class Session:
    date: dt.date
    start: dt.datetime
    end: dt.datetime
    course: str


# ------------------------------------------------------------------ planning
def course_weight(course, day):
    """How much study time a course deserves on a given day."""
    if course.exam is None:
        return float(course.units)
    days_left = (course.exam - day).days
    if days_left <= 0:                     # exam day or later: the course is done
        return 0.0
    if days_left <= EXAM_BOOST_DAYS:       # exam coming up: ramp up its share
        return course.units * (1 + EXAM_BOOST_MAX * (1 - (days_left - 1) / EXAM_BOOST_DAYS))
    return float(course.units)


def sessions_per_day(s):
    return int((s.hours_per_day * 60 + s.break_min) // (s.session_min + s.break_min))


def build_plan(courses, s):
    """Smooth weighted round-robin: every course gets sessions in proportion
    to its weight, and courses alternate instead of being bunched together."""
    plan = []
    credit = {c.name: 0.0 for c in courses}
    per_day = sessions_per_day(s)
    for offset in range(s.days):
        day = s.start_date + dt.timedelta(days=offset)
        if day.weekday() in s.rest_days:
            continue
        weights = {c.name: course_weight(c, day) for c in courses}
        active = [name for name, w in weights.items() if w > 0]
        if not active:
            continue
        total = sum(weights[name] for name in active)
        t = dt.datetime.combine(day, s.day_start)
        for _ in range(per_day):
            for name in active:
                credit[name] += weights[name]
            best = max(active, key=lambda name: credit[name])
            credit[best] -= total
            end = t + dt.timedelta(minutes=s.session_min)
            plan.append(Session(day, t, end, best))
            t = end + dt.timedelta(minutes=s.break_min)
    return plan


# ---------------------------------------------------------------- formatting
def fmt_minutes(m):
    h, mm = divmod(int(m), 60)
    return f"{h}h {mm:02d}m"


def summary_lines(plan, courses, s):
    minutes = {c.name: 0 for c in courses}
    for x in plan:
        minutes[x.course] += s.session_min
    study_days = len({x.date for x in plan})
    end = s.start_date + dt.timedelta(days=s.days - 1)
    width = max(len(c.name) for c in courses)
    biggest = max(minutes.values()) or 1
    rest = ", ".join(WEEKDAYS[d].capitalize() for d in sorted(s.rest_days)) or "none"
    lines = [
        f"Plan:   {s.start_date} to {end}  ({study_days} study days, rest: {rest})",
        f"Daily:  {sessions_per_day(s)} x {s.session_min} min focus with "
        f"{s.break_min} min breaks, starting {s.day_start:%H:%M}",
        f"Total:  {fmt_minutes(sum(minutes.values()))} of focused study",
        "",
    ]
    for c in courses:
        share = minutes[c.name]
        bar = "█" * max(1, round(24 * share / biggest)) if share else ""
        exam = f"   exam {c.exam:%Y-%m-%d}" if c.exam else ""
        lines.append(f"  {c.name:<{width}}  {fmt_minutes(share):>9}  {bar:<24}{exam}")
    return lines


def day_lines(plan, courses, max_days=None):
    exams = {}
    for c in courses:
        if c.exam:
            exams.setdefault(c.exam, []).append(c.name)
    lines, current, shown = [], None, 0
    for x in plan:
        if x.date != current:
            if max_days is not None and shown == max_days:
                break
            current = x.date
            shown += 1
            lines.append("")
            lines.append(f"{x.date:%A %Y-%m-%d}")
            if x.date in exams:
                lines.append(f"  ** EXAM: {', '.join(exams[x.date])} **")
            lines.append("-" * 30)
        lines.append(f"  {x.start:%H:%M}-{x.end:%H:%M}  {x.course}")
    return lines


# ------------------------------------------------------------------- writers
def write_txt(path, plan, courses, s):
    with open(path, "w", encoding="utf-8") as f:
        f.write("STUDY PLAN\n==========\n\n")
        f.write("\n".join(summary_lines(plan, courses, s)) + "\n")
        f.write("\n".join(day_lines(plan, courses)) + "\n")


def write_csv(path, plan):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:   # BOM so Excel reads UTF-8
        w = csv.writer(f)
        w.writerow(["date", "weekday", "start", "end", "course"])
        for x in plan:
            w.writerow([x.date.isoformat(), f"{x.date:%A}", f"{x.start:%H:%M}",
                        f"{x.end:%H:%M}", x.course])


def ics_text(value):
    return (value.replace("\\", "\\\\").replace(";", "\\;")
                 .replace(",", "\\,").replace("\n", "\\n"))


def write_ics(path, plan, courses):
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0",
             "PRODID:-//Study Plan Generator//EN", "CALSCALE:GREGORIAN"]
    for x in plan:
        lines += ["BEGIN:VEVENT",
                  f"UID:{uuid.uuid4()}@study-plan-generator",
                  f"DTSTAMP:{stamp}",
                  f"DTSTART:{x.start:%Y%m%dT%H%M%S}",
                  f"DTEND:{x.end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:{ics_text('Study: ' + x.course)}",
                  "END:VEVENT"]
    for c in courses:
        if c.exam:
            lines += ["BEGIN:VEVENT",
                      f"UID:{uuid.uuid4()}@study-plan-generator",
                      f"DTSTAMP:{stamp}",
                      f"DTSTART;VALUE=DATE:{c.exam:%Y%m%d}",
                      f"DTEND;VALUE=DATE:{c.exam + dt.timedelta(days=1):%Y%m%d}",
                      f"SUMMARY:{ics_text('EXAM: ' + c.name)}",
                      "END:VEVENT"]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(lines) + "\r\n")


# --------------------------------------------------------------------- input
def ask(prompt, convert, default=None, check=None, error="Invalid value, please try again."):
    """Keep asking until the answer converts and passes the check."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if not raw and default is not None:
            raw = str(default)
        try:
            value = convert(raw)
        except ValueError:
            print(f"  ! {error}")
            continue
        if check is not None and not check(value):
            print(f"  ! {error}")
            continue
        return value


def non_empty(raw):
    if not raw:
        raise ValueError
    return raw


def parse_date(raw):
    return dt.date.fromisoformat(raw)


def parse_optional_date(raw):
    return dt.date.fromisoformat(raw) if raw else None


def parse_time(raw):
    return dt.datetime.strptime(raw, "%H:%M").time()


def parse_rest_days(raw):
    raw = raw.lower()
    if raw in ("none", "no", "-"):
        return set()
    days = set()
    for part in raw.replace(",", " ").split():
        match = [i for i, name in enumerate(WEEKDAYS) if len(part) >= 3 and name.startswith(part)]
        if len(match) != 1:
            raise ValueError
        days.add(match[0])
    return days


def read_input():
    today = dt.date.today()
    print("Press Enter to accept the default shown in [brackets].\n")

    start = ask("Start date (YYYY-MM-DD)", parse_date, default=today.isoformat(),
                error="Use the format YYYY-MM-DD.")
    days = ask("How many days should the plan cover", int, default=120,
               check=lambda v: 1 <= v <= 730, error="Enter a number from 1 to 730.")
    n = ask("How many courses", int,
            check=lambda v: 1 <= v <= 30, error="Enter a number from 1 to 30.")

    courses = []
    for i in range(1, n + 1):
        print(f"\nCourse {i} of {n}")
        taken = {c.name.lower() for c in courses}
        name = ask("  Name", non_empty, check=lambda v: v.lower() not in taken,
                   error="Enter a name that isn't used yet.")
        units = ask("  Units", int, check=lambda v: 1 <= v <= 10,
                    error="Enter a number from 1 to 10.")
        exam = ask("  Exam date (YYYY-MM-DD, or Enter to skip)", parse_optional_date,
                   check=lambda v: v is None or v > start,
                   error="Use YYYY-MM-DD after the start date, or leave it empty.")
        courses.append(Course(name, units, exam))

    print()
    hours = ask("Study hours per day, breaks included", float, default=4,
                check=lambda v: 0.5 <= v <= 16, error="Enter a number from 0.5 to 16.")
    session = ask("Focus session length in minutes", int, default=50,
                  check=lambda v: 10 <= v <= 180 and v <= hours * 60,
                  error="Enter 10-180 minutes, and no more than your daily study time.")
    brk = ask("Break between sessions in minutes", int, default=10,
              check=lambda v: 0 <= v <= 60, error="Enter a number from 0 to 60.")
    day_start = ask("Start studying at (HH:MM)", parse_time, default="09:00",
                    check=lambda t: t.hour * 60 + t.minute + hours * 60 <= 24 * 60,
                    error="Use HH:MM, and make sure your study day ends before midnight.")
    rest = ask("Rest days with no study (e.g. friday, 'sat sun', or none)", parse_rest_days,
               default="friday", check=lambda d: len(d) < 7,
               error="Use weekday names like friday or 'sat sun', or none.")

    return courses, Settings(start, days, hours, day_start, session, brk, rest)


# ---------------------------------------------------------------------- main
def main():
    print("=" * 44)
    print("  STUDY PLAN GENERATOR")
    print("=" * 44)
    try:
        courses, s = read_input()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        return

    plan = build_plan(courses, s)
    if not plan:
        print("\nNothing to schedule: every exam is over or every day is a rest day.")
        return

    print()
    print("\n".join(summary_lines(plan, courses, s)))
    print("\nYour first days:")
    print("\n".join(day_lines(plan, courses, max_days=3)))

    try:
        write_txt("study_plan.txt", plan, courses, s)
        write_csv("study_plan.csv", plan)
        write_ics("study_plan.ics", plan, courses)
    except OSError as e:
        print(f"\nCould not save the files: {e}")
        return

    print("\nSaved:")
    print("  study_plan.txt  readable schedule")
    print("  study_plan.csv  open in Excel or Google Sheets")
    print("  study_plan.ics  import into Google Calendar / Outlook / Apple Calendar")


if __name__ == "__main__":
    main()
