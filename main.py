from datetime import datetime, timedelta
from pawpal_system import Owner, Task, TaskType, Frequency, Status

# ── Setup ─────────────────────────────────────────────────────────────────────

owner = Owner(
    first_name="Maria",
    last_name="Santos",
    email="maria@pawpal.com",
    phone="555-4321",
    address="42 Maple Avenue",
)

fido    = owner.create_pet("Fido",    animal_type="Dog")
luna    = owner.create_pet("Luna",    animal_type="Cat")

fido.update_info(breed="Golden Retriever", age=3, gender="Male",   weight=32.0)
luna.update_info(breed="Siamese",          age=5, gender="Female", weight=4.2)

# ── Tasks ─────────────────────────────────────────────────────────────────────

morning_walk = Task(
    type=TaskType.WALKING,
    name="Morning Walk",
    description="30-minute walk around the block",
    duration_minutes=30,
    priority=3,
    frequency=Frequency.DAILY,
)

breakfast = Task(
    type=TaskType.FEEDING,
    name="Breakfast",
    description="One cup of dry kibble",
    duration_minutes=10,
    priority=5,
    frequency=Frequency.DAILY,
)

luna_grooming = Task(
    type=TaskType.GROOMING,
    name="Brush Luna",
    description="Full coat brushing",
    duration_minutes=20,
    priority=2,
    frequency=Frequency.WEEKLY,
)

fido_bath = Task(
    type=TaskType.BATHING,
    name="Bath Time",
    description="Full wash and dry",
    duration_minutes=45,
    priority=1,
    frequency=Frequency.WEEKLY,
)

luna_medication = Task(
    type=TaskType.MEDICATION,
    name="Luna's Vitamins",
    description="Daily vitamin supplement mixed into food",
    duration_minutes=5,
    priority=4,
    frequency=Frequency.DAILY,
)

# ── Assign tasks to pets ──────────────────────────────────────────────────────

owner.assign_task_to_pet(fido, morning_walk)
owner.assign_task_to_pet(fido, breakfast)
owner.assign_task_to_pet(fido, fido_bath)

owner.assign_task_to_pet(luna, luna_grooming)
owner.assign_task_to_pet(luna, luna_medication)

# ── Schedule tasks for today ──────────────────────────────────────────────────

today     = datetime.now()
at_7am    = today.replace(hour=7,  minute=0, second=0, microsecond=0)
at_8am    = today.replace(hour=8,  minute=0, second=0, microsecond=0)
at_9am    = today.replace(hour=9,  minute=0, second=0, microsecond=0)
at_11am   = today.replace(hour=11, minute=0, second=0, microsecond=0)
at_6pm    = today.replace(hour=18, minute=0, second=0, microsecond=0)

scheduler = owner.scheduler

# Fido: breakfast at 7 AM, walk at 8 AM, bath at 11 AM
scheduler.assign_task_to_schedule(fido, breakfast,     today, at_7am)
scheduler.assign_task_to_schedule(fido, morning_walk,  today, at_8am)
scheduler.assign_task_to_schedule(fido, fido_bath,     today, at_11am)

# Luna: vitamins at 8 AM (same clock-hour is fine — different pet),
#        grooming at 6 PM
scheduler.assign_task_to_schedule(luna, luna_medication, today, at_8am)
scheduler.assign_task_to_schedule(luna, luna_grooming,   today, at_6pm)

# ── Print today's schedule ────────────────────────────────────────────────────

today_str = today.strftime("%Y-%m-%d")

print("=" * 58)
print(f"  PawPal+ | Today's Schedule  ({today_str})")
print(f"  Owner: {owner.first_name} {owner.last_name}")
print("=" * 58)

todays_slots = [
    entry
    for entry in scheduler.view_schedule()
    if entry["date"] == today_str
]

has_any = False
for entry in todays_slots:
    if not entry["available"]:
        has_any = True
        print(f"\n  {entry['time']}")
        for booking in entry["bookings"]:
            stars = "*" * booking["priority"]
            print(f"    [{stars}] {booking['pet_name']:8s} | "
                  f"{booking['task_type']:10s} | "
                  f"{booking['task_name']:20s} | "
                  f"{booking['duration_minutes']} min  "
                  f"[{booking['task_status']}]")

if not has_any:
    print("\n  No tasks scheduled for today.")

print("\n" + "=" * 58)
print("  Priority key:  * low  ->  ***** high")
print("=" * 58)

# ── Priority overview (all scheduled tasks, sorted) ───────────────────────────

print("\n  -- Tasks by Priority (all scheduled) --\n")
for i, entry in enumerate(scheduler.view_tasks_by_priority(), start=1):
    print(f"  {i}. [priority {entry['priority']}] {entry['pet_name']:8s} | "
          f"{entry['task_name']:20s} | "
          f"{entry['scheduled_date']}  {entry['scheduled_time']}  "
          f"[{entry['task_status']}]")

print()
