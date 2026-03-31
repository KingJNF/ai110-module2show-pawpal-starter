"""
Main.py — PawPal+ Testing Ground (Timezone-Aware)

Demonstrates all features using timezone-aware datetimes via ZoneInfo.
"""

from pawpal_system import (
    Owner, Pet, Task, Scheduler,
    TaskType, Frequency, Status, DEFAULT_DURATIONS,
)
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


# ── Helper ───────────────────────────────────────────────────────────
def print_header(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def print_task_row(t: dict, show_date: bool = False):
    date_col = f"{t['scheduled_date']} " if show_date else ""
    tz_col = f" {t.get('timezone', '')}" if t.get('timezone') else ""
    print(
        f"  {date_col}{t['scheduled_time']}–{t['end_time']}{tz_col} | "
        f"{t['pet_name']:10s} | {t['task_name']:22s} | "
        f"Pri: {t['priority']:2d} | {t['status']}"
    )


# ── Main ─────────────────────────────────────────────────────────────
def main():
    # ==================================================================
    # SETUP: Owner with timezone, Pets, Scheduler
    # ==================================================================
    eastern = ZoneInfo("America/New_York")

    owner = Owner(
        first_name="Jane",
        last_name="Doe",
        email="jane@email.com",
        phone="555-0001",
        address="456 Oak St",
        tz=eastern,
    )
    dog = owner.create_pet("Buddy", "Dog")
    cat = owner.create_pet("Whiskers", "Cat")
    scheduler = owner.scheduler

    print_header("TIMEZONE CONFIGURATION")
    print(f"  Owner timezone:    {owner.tz}")
    print(f"  Scheduler timezone: {scheduler.tz}")
    print(f"  Current time:      {scheduler.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Tomorrow as the scheduling target (timezone-aware)
    tomorrow = scheduler.now().replace(
        hour=0, minute=0, second=0, microsecond=0
    ) + timedelta(days=1)

    print(f"  Scheduling date:   {tomorrow.strftime('%Y-%m-%d %Z')}")

    # ==================================================================
    # CREATE TASKS — deliberately OUT OF chronological ORDER
    # ==================================================================

    # ---- Dog tasks ----
    afternoon_walk = Task(
        type=TaskType.WALKING,
        name="Afternoon Walk",
        description="Walk around the neighborhood",
        duration_minutes=DEFAULT_DURATIONS[TaskType.WALKING],
        priority=8,
        frequency=Frequency.DAILY,
    )
    morning_feed = Task(
        type=TaskType.FEEDING,
        name="Morning Feeding",
        description="Breakfast kibble in puzzle feeder",
        duration_minutes=DEFAULT_DURATIONS[TaskType.FEEDING],
        priority=9,
        frequency=Frequency.DAILY,
    )
    grooming = Task(
        type=TaskType.GROOMING,
        name="Brush Fur",
        description="Brush coat and check for tangles",
        duration_minutes=DEFAULT_DURATIONS[TaskType.GROOMING],
        priority=5,
        frequency=Frequency.WEEKLY,
    )
    evening_meds = Task(
        type=TaskType.MEDICATION,
        name="Evening Medication",
        description="Joint supplement — daily for 2 weeks",
        duration_minutes=DEFAULT_DURATIONS[TaskType.MEDICATION],
        priority=10,
        frequency=Frequency.CUSTOM,
        repeat_count=14,
        repeat_interval_days=1,
    )

    # ---- Cat tasks ----
    cat_breakfast = Task(
        type=TaskType.FEEDING,
        name="Cat Breakfast",
        description="Wet food with vitamins",
        duration_minutes=DEFAULT_DURATIONS[TaskType.FEEDING],
        priority=9,
        frequency=Frequency.DAILY,
    )

    # *** CONFLICT TASK: same time as dog's Afternoon Walk ***
    cat_playtime = Task(
        type=TaskType.ENRICHMENT,
        name="Cat Playtime",
        description="Feather wand session",
        duration_minutes=DEFAULT_DURATIONS[TaskType.ENRICHMENT],
        priority=7,
        frequency=Frequency.DAILY,
    )

    # ==================================================================
    # ASSIGN TASKS TO PETS (out of order)
    # ==================================================================
    owner.assign_task_to_pet(dog, afternoon_walk)
    owner.assign_task_to_pet(dog, morning_feed)
    owner.assign_task_to_pet(dog, grooming)
    owner.assign_task_to_pet(dog, evening_meds)
    owner.assign_task_to_pet(cat, cat_breakfast)
    owner.assign_task_to_pet(cat, cat_playtime)

    # ==================================================================
    # SCHEDULE TASKS (out of chronological order, timezone-aware)
    # ==================================================================
    scheduler.assign_task_to_schedule(
        dog, afternoon_walk, tomorrow, tomorrow.replace(hour=14, minute=0)
    )
    scheduler.assign_task_to_schedule(
        dog, morning_feed, tomorrow, tomorrow.replace(hour=8, minute=0)
    )
    scheduler.assign_task_to_schedule(
        dog, grooming, tomorrow, tomorrow.replace(hour=10, minute=0)
    )
    scheduler.assign_task_to_schedule(
        dog, evening_meds, tomorrow, tomorrow.replace(hour=18, minute=0)
    )
    scheduler.assign_task_to_schedule(
        cat, cat_breakfast, tomorrow, tomorrow.replace(hour=8, minute=30)
    )
    # Cross-pet conflict: Cat Playtime at 2:00 PM = same as dog's walk
    scheduler.assign_task_to_schedule(
        cat, cat_playtime, tomorrow, tomorrow.replace(hour=14, minute=0)
    )

    # ==================================================================
    # DEMO 1: SORT ALL TASKS BY TIME
    # ==================================================================
    print_header("ALL TASKS SORTED BY TIME (added out of order)")
    sorted_tasks = scheduler.sort_tasks_by_time()
    for t in sorted_tasks:
        print_task_row(t)

    # ==================================================================
    # DEMO 2: FILTER BY PET
    # ==================================================================
    print_header("FILTER → Buddy's Tasks Only")
    for t in scheduler.filter_tasks(pet=dog):
        print_task_row(t)

    print_header("FILTER → Whiskers' Tasks Only")
    for t in scheduler.filter_tasks(pet=cat):
        print_task_row(t)

    # ==================================================================
    # DEMO 3: FILTER BY STATUS
    # ==================================================================
    print_header("FILTER → Pending Tasks Only")
    for t in scheduler.filter_tasks(status=Status.PENDING):
        print_task_row(t)

    # ==================================================================
    # DEMO 4: FILTER BY PET + STATUS
    # ==================================================================
    print_header("FILTER → Buddy's Pending Tasks Only")
    for t in scheduler.filter_tasks(pet=dog, status=Status.PENDING):
        print_task_row(t)

    # ==================================================================
    # DEMO 5: CONFLICT DETECTION
    # ==================================================================
    print_header("CONFLICT DETECTION (warns, never crashes)")
    warnings = scheduler.detect_conflicts()
    if warnings:
        for w in warnings:
            print(f"  {w}")
        print(f"\n  Total conflicts found: {len(warnings)}")
    else:
        print("  ✅ No conflicts detected.")

    # ==================================================================
    # DEMO 6: COMPLETE DAILY TASK → AUTO-RENEW (timedelta)
    # ==================================================================
    print_header("RECURRING TASK → COMPLETE & AUTO-RENEW")

    print(f"  Task:      '{morning_feed.name}'")
    print(f"  Frequency: {morning_feed.frequency.value}")
    print(f"  Original:  {morning_feed.scheduled_date.strftime('%Y-%m-%d')} at "
          f"{morning_feed.scheduled_time.strftime('%H:%M %Z')}")
    print(f"  Completing task...")

    new_task = scheduler.complete_and_renew(dog, morning_feed)

    print(f"  Old status: {morning_feed.status.value} ✅")
    if new_task:
        print(f"\n  ✅ New occurrence auto-created:")
        print(f"     Name:      '{new_task.name}'")
        print(f"     Scheduled: {new_task.scheduled_date.strftime('%Y-%m-%d')} at "
              f"{new_task.scheduled_time.strftime('%H:%M %Z')}")
        print(f"     Status:    {new_task.status.value}")
        expected_date = (tomorrow + timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"     (timedelta: original {tomorrow.strftime('%Y-%m-%d')} + 1 day = {expected_date})")
    else:
        print("  ❌ Could not auto-renew.")

    # ==================================================================
    # DEMO 7: COMPLETE CUSTOM TASK → AUTO-RENEW (medication)
    # ==================================================================
    print_header("CUSTOM RECURRING → COMPLETE & AUTO-RENEW (medication)")

    print(f"  Task:           '{evening_meds.name}'")
    print(f"  Frequency:      {evening_meds.frequency.value} "
          f"(every {evening_meds.repeat_interval_days} day(s), "
          f"{evening_meds.repeat_count} total)")
    print(f"  Completed so far: {evening_meds.occurrences_completed}")
    print(f"  Completing task...")

    new_med = scheduler.complete_and_renew(dog, evening_meds)

    print(f"  Old status: {evening_meds.status.value} ✅")
    print(f"  Occurrences completed: {evening_meds.occurrences_completed}")
    if new_med:
        print(f"\n  ✅ Next medication occurrence auto-created:")
        print(f"     Scheduled: {new_med.scheduled_date.strftime('%Y-%m-%d')} at "
              f"{new_med.scheduled_time.strftime('%H:%M %Z')}")
        print(f"     Remaining: {new_med.repeat_count - new_med.occurrences_completed} more")
    else:
        print("  ❌ Could not auto-renew.")

    # ==================================================================
    # DEMO 8: FINAL SORTED VIEW (including timezone in output)
    # ==================================================================
    print_header("FINAL SCHEDULE — ALL TASKS (including renewed)")
    for t in scheduler.sort_tasks_by_time():
        print_task_row(t, show_date=True)

    # ==================================================================
    # DEMO 9: COMPLETED TASKS
    # ==================================================================
    print_header("COMPLETED TASKS")
    completed = scheduler.filter_tasks(status=Status.COMPLETED)
    if completed:
        for t in completed:
            print_task_row(t, show_date=True)
    else:
        print("  No completed tasks yet.")

    # ==================================================================
    # DEMO 10: SCHEDULE EXPLANATION
    # ==================================================================
    print_header("SCHEDULE EXPLANATION (why & when each task was chosen)")
    for explanation in scheduler.explain_schedule():
        print(f"  {explanation}")


if __name__ == "__main__":
    main()