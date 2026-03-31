from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from enum import Enum
from zoneinfo import ZoneInfo


# ===================================================================
# Enums
# ===================================================================

class TaskType(Enum):
    FEEDING = "Feeding"
    WALKING = "Walking"
    BATHING = "Bathing"
    GROOMING = "Grooming"
    MEDICATION = "Medication"
    ENRICHMENT = "Enrichment"


class Frequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


# Realistic default durations (minutes) per task type
DEFAULT_DURATIONS = {
    TaskType.FEEDING: 5,
    TaskType.MEDICATION: 5,
    TaskType.WALKING: 30,
    TaskType.BATHING: 45,
    TaskType.GROOMING: 30,
    TaskType.ENRICHMENT: 20,
}

# Default timezone — UTC is the safest default
DEFAULT_TZ = ZoneInfo("UTC")


# ===================================================================
# Task
# ===================================================================

@dataclass
class Task:
    type: TaskType
    name: str
    description: str
    duration_minutes: int
    priority: int                               # 1-10, higher = more important
    frequency: Frequency = Frequency.ONCE
    repeat_count: Optional[int] = None          # CUSTOM: total occurrences
    repeat_interval_days: Optional[int] = None  # CUSTOM: days between repeats
    occurrences_completed: int = 0
    status: Status = Status.PENDING
    scheduled_date: Optional[datetime] = None
    scheduled_time: Optional[datetime] = None
    pet: Optional['Pet'] = None

    def assign_task(self):
        """Mark the task as in-progress."""
        self.status = Status.IN_PROGRESS

    def complete_task(self):
        """Mark the task as completed and increment occurrence counter."""
        self.status = Status.COMPLETED
        self.occurrences_completed += 1

    def reset_task(self):
        """Reset the task status back to pending."""
        self.status = Status.PENDING

    def _get_start_datetime(self) -> Optional[datetime]:
        """Combine scheduled_date and scheduled_time into one timezone-aware datetime."""
        if self.scheduled_date is None or self.scheduled_time is None:
            return None
        dt = datetime(
            self.scheduled_date.year,
            self.scheduled_date.month,
            self.scheduled_date.day,
            self.scheduled_time.hour,
            self.scheduled_time.minute,
            self.scheduled_time.second,
        )
        # Preserve timezone if already set, otherwise attach UTC
        if dt.tzinfo is None:
            if self.scheduled_date.tzinfo is not None:
                dt = dt.replace(tzinfo=self.scheduled_date.tzinfo)
            elif self.scheduled_time.tzinfo is not None:
                dt = dt.replace(tzinfo=self.scheduled_time.tzinfo)
            else:
                dt = dt.replace(tzinfo=DEFAULT_TZ)
        return dt

    def get_end_datetime(self) -> Optional[datetime]:
        """Calculate when this task ends based on start time + duration."""
        start = self._get_start_datetime()
        if start is None:
            return None
        return start + timedelta(minutes=self.duration_minutes)

    def is_due(self) -> bool:
        """Return True if the task's scheduled datetime has passed (timezone-aware)."""
        start = self._get_start_datetime()
        if start is None:
            return False
        now = datetime.now(tz=start.tzinfo or timezone.utc)
        return now >= start

    def is_recurring(self) -> bool:
        """Return True if this task repeats."""
        return self.frequency != Frequency.ONCE

    def needs_more_occurrences(self) -> bool:
        """Return True if recurring task still has future occurrences needed."""
        if self.frequency == Frequency.CUSTOM and self.repeat_count is not None:
            return self.occurrences_completed < self.repeat_count
        if self.frequency in (Frequency.DAILY, Frequency.WEEKLY, Frequency.MONTHLY):
            return True
        return False


# ===================================================================
# Pet
# ===================================================================

@dataclass
class Pet:
    name: str
    animal_type: Optional[str] = None
    breed: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    weight: Optional[float] = None
    owner: Optional['Owner'] = None
    tasks: List[Task] = field(default_factory=list)

    def update_info(
        self,
        *,
        animal_type: Optional[str] = None,
        breed: Optional[str] = None,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        weight: Optional[float] = None,
    ):
        """Update any provided pet profile fields."""
        if animal_type is not None:
            self.animal_type = animal_type
        if breed is not None:
            self.breed = breed
        if age is not None:
            self.age = age
        if gender is not None:
            self.gender = gender
        if weight is not None:
            self.weight = weight

    def add_task(self, task: Task):
        """Add a task, enforcing no duplicate pending/in-progress of the same type
        (recurring tasks are exempt)."""
        if task in self.tasks:
            raise ValueError("Task already assigned to this pet.")

        if not task.is_recurring():
            for existing in self.tasks:
                if (
                    existing.type == task.type
                    and existing.status in {Status.PENDING, Status.IN_PROGRESS}
                    and not existing.is_recurring()
                ):
                    raise ValueError(
                        f"Cannot add duplicate pending/in-progress task of type "
                        f"{task.type.value} for the same pet."
                    )

        self.tasks.append(task)
        task.pet = self

    def remove_task(self, task: Task):
        """Remove a task from the pet."""
        if task not in self.tasks:
            raise ValueError("Task is not assigned to this pet.")
        self.tasks.remove(task)
        task.pet = None

    def get_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def summary(self) -> dict:
        """Return a dict of the pet's profile and task status counts."""
        return {
            "name": self.name,
            "animal_type": self.animal_type,
            "breed": self.breed,
            "age": self.age,
            "gender": self.gender,
            "weight": self.weight,
            "task_count": len(self.tasks),
            "pending": len([t for t in self.tasks if t.status == Status.PENDING]),
            "in_progress": len([t for t in self.tasks if t.status == Status.IN_PROGRESS]),
            "completed": len([t for t in self.tasks if t.status == Status.COMPLETED]),
        }


# ===================================================================
# Owner
# ===================================================================

class Owner:
    def __init__(
        self,
        first_name: str,
        last_name: str,
        email: str,
        phone: str,
        address: str,
        tz: Optional[ZoneInfo] = None,
    ):
        """Initialize a new Owner with contact details and a timezone.
        Timezone defaults to UTC if not provided."""
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.tz = tz or DEFAULT_TZ
        self.pets: List[Pet] = []
        self.scheduler = Scheduler(self, tz=self.tz)

    def create_pet(self, name: str, animal_type: Optional[str] = None) -> Pet:
        """Create a new Pet owned by this owner."""
        pet = Pet(name=name, animal_type=animal_type, owner=self)
        self.pets.append(pet)
        return pet

    def view_pet_tasks(self, pet: Pet) -> List[Task]:
        if pet.owner != self:
            raise ValueError("You can only view tasks for your own pets.")
        return pet.get_tasks()

    def view_tasks_for_pets(self, pets: List[Pet]) -> List[Task]:
        combined: List[Task] = []
        for pet in pets:
            if pet.owner != self:
                raise ValueError("You can only view tasks for your own pets.")
            combined.extend(pet.get_tasks())
        return combined

    def assign_task_to_pet(self, pet: Pet, task: Task):
        if pet.owner != self:
            raise ValueError("You can only assign tasks to your own pets.")
        pet.add_task(task)

    def modify_info(
        self,
        *,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        address: Optional[str] = None,
    ):
        if first_name is not None:
            self.first_name = first_name
        if last_name is not None:
            self.last_name = last_name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if address is not None:
            self.address = address

    def get_info(self) -> dict:
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "timezone": str(self.tz),
            "pet_count": len(self.pets),
        }

    def view_pet_info(self, pet: Pet) -> dict:
        if pet.owner != self:
            raise ValueError("You can only view info for your own pets.")
        return pet.summary()

    def view_all_pets(self) -> List[dict]:
        return [pet.summary() for pet in self.pets]


# ===================================================================
# Scheduler
# ===================================================================

class Scheduler:
    SCHEDULE_START_HOUR = 8   # 8 AM
    SCHEDULE_END_HOUR = 20    # 8 PM
    SLOT_MINUTES = 30         # display slot granularity

    def __init__(self, owner: 'Owner', tz: Optional[ZoneInfo] = None):
        """Initialize the Scheduler with an owner and a timezone.
        All internal datetimes will be created with this timezone."""
        self.owner = owner
        self.tz = tz or DEFAULT_TZ
        self.schedule: dict = {}

    # ------------------------------------------------------------------
    # Timezone helper
    # ------------------------------------------------------------------

    def now(self) -> datetime:
        """Return the current timezone-aware datetime in the scheduler's timezone."""
        return datetime.now(tz=self.tz)

    def _make_aware(self, dt: datetime) -> datetime:
        """Ensure a datetime has timezone info. If naive, attach the scheduler's tz."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self.tz)
        return dt

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _to_slot(self, date: datetime, time: datetime) -> datetime:
        """Combine separate date and time objects into a single timezone-aware datetime."""
        dt = datetime(
            date.year, date.month, date.day,
            time.hour, time.minute, time.second,
            tzinfo=self.tz,
        )
        return dt

    def _booking_entry(self, pet: 'Pet', task: Task) -> dict:
        return {
            "pet_name": pet.name,
            "task_name": task.name,
            "task_type": task.type.value,
            "priority": task.priority,
            "duration_minutes": task.duration_minutes,
            "task_status": task.status.value,
        }

    def _all_owner_tasks(self) -> List[Tuple['Pet', Task]]:
        pairs = []
        for pet in self.owner.pets:
            for task in pet.tasks:
                pairs.append((pet, task))
        return pairs

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _check_time_bounds(self, slot: datetime, duration_minutes: int):
        """Ensure the entire task fits within the 8 AM – 8 PM window."""
        slot = self._make_aware(slot)
        start_hour = slot.hour + slot.minute / 60.0
        end_dt = slot + timedelta(minutes=duration_minutes)
        end_hour = end_dt.hour + end_dt.minute / 60.0
        if end_dt.date() > slot.date():
            end_hour = 24.0

        if start_hour < self.SCHEDULE_START_HOUR:
            raise ValueError(
                f"Cannot schedule before {self.SCHEDULE_START_HOUR}:00 AM."
            )
        if end_hour > self.SCHEDULE_END_HOUR:
            raise ValueError(
                f"Task would end at {end_dt.strftime('%H:%M')}, "
                f"which is past the {self.SCHEDULE_END_HOUR}:00 cutoff."
            )

    def _check_overlap(self, pet: 'Pet', task: Task, candidate_start: datetime):
        """Duration-aware overlap detection for a specific pet's schedule."""
        candidate_start = self._make_aware(candidate_start)
        candidate_end = candidate_start + timedelta(minutes=task.duration_minutes)

        for existing in pet.tasks:
            if existing is task:
                continue
            if existing.scheduled_date is None or existing.scheduled_time is None:
                continue
            if existing.status == Status.COMPLETED:
                continue

            existing_start = self._to_slot(existing.scheduled_date, existing.scheduled_time)
            existing_end = existing_start + timedelta(minutes=existing.duration_minutes)

            if candidate_start < existing_end and candidate_end > existing_start:
                raise ValueError(
                    f"Time conflict with '{existing.name}': it runs "
                    f"{existing_start.strftime('%H:%M')}–{existing_end.strftime('%H:%M')}. "
                    f"Your task would run "
                    f"{candidate_start.strftime('%H:%M')}–{candidate_end.strftime('%H:%M')}."
                )

            if existing.type == task.type:
                if abs((existing_end - candidate_start).total_seconds()) <= 60:
                    raise ValueError(
                        f"Cannot schedule {task.type.value} back-to-back; "
                        f"'{existing.name}' ends at {existing_end.strftime('%H:%M')}."
                    )

    def _is_slot_free(self, pet: 'Pet', start: datetime, duration_minutes: int,
                      exclude_task: Optional[Task] = None) -> bool:
        """Quick boolean check: can a task of given duration fit at this time?"""
        start = self._make_aware(start)
        end = start + timedelta(minutes=duration_minutes)

        start_hour = start.hour + start.minute / 60.0
        end_hour = end.hour + end.minute / 60.0
        if end.date() > start.date():
            end_hour = 24.0
        if start_hour < self.SCHEDULE_START_HOUR or end_hour > self.SCHEDULE_END_HOUR:
            return False

        for existing in pet.tasks:
            if existing is exclude_task:
                continue
            if existing.scheduled_date is None or existing.scheduled_time is None:
                continue
            if existing.status == Status.COMPLETED:
                continue
            ex_start = self._to_slot(existing.scheduled_date, existing.scheduled_time)
            ex_end = ex_start + timedelta(minutes=existing.duration_minutes)
            if start < ex_end and end > ex_start:
                return False
        return True

    # ------------------------------------------------------------------
    # Build / refresh internal schedule
    # ------------------------------------------------------------------

    def build_schedule(self, pets: List['Pet']) -> dict:
        """Seed a 7-day schedule with 30-min display slots (8 AM–8 PM, timezone-aware)."""
        for pet in pets:
            if pet.owner != self.owner:
                raise ValueError("You can only build schedules for your own pets.")

        base_date = self.now().replace(
            hour=self.SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0
        )
        schedule: dict = {}
        total_hours = self.SCHEDULE_END_HOUR - self.SCHEDULE_START_HOUR
        slots_per_day = (total_hours * 60) // self.SLOT_MINUTES

        for day in range(7):
            for s in range(slots_per_day):
                slot = base_date + timedelta(days=day, minutes=s * self.SLOT_MINUTES)
                schedule[slot] = []

        for pet in pets:
            for task in pet.tasks:
                if task.scheduled_date and task.scheduled_time:
                    task_start = self._to_slot(task.scheduled_date, task.scheduled_time)
                    task_end = task_start + timedelta(minutes=task.duration_minutes)
                    for slot in schedule:
                        slot_end = slot + timedelta(minutes=self.SLOT_MINUTES)
                        if task_start < slot_end and task_end > slot:
                            schedule[slot].append(self._booking_entry(pet, task))

        self.schedule = schedule
        return schedule

    # ------------------------------------------------------------------
    # Viewing the schedule
    # ------------------------------------------------------------------

    def view_schedule(self, pets: Optional[List['Pet']] = None) -> List[dict]:
        target_pets = pets if pets is not None else list(self.owner.pets)
        self.build_schedule(target_pets)

        result = []
        for slot in sorted(self.schedule):
            bookings = self.schedule[slot]
            tz_label = slot.strftime("%Z") or str(self.tz)
            result.append({
                "slot": slot,
                "date": slot.strftime("%Y-%m-%d"),
                "time": slot.strftime("%H:%M"),
                "timezone": tz_label,
                "available": len(bookings) == 0,
                "bookings": sorted(bookings, key=lambda b: b["priority"], reverse=True),
            })
        return result

    def get_available_slots(
        self,
        pets: Optional[List['Pet']] = None,
        date: Optional[datetime] = None,
    ) -> List[dict]:
        all_slots = self.view_schedule(pets)
        free = [s for s in all_slots if s["available"]]
        if date is not None:
            free = [s for s in free if s["date"] == date.strftime("%Y-%m-%d")]
        return free

    def get_slot_info(self, date: datetime, time: datetime) -> dict:
        self.build_schedule(list(self.owner.pets))
        slot = self._to_slot(date, time)
        bookings = self.schedule.get(slot, [])

        if slot not in self.schedule:
            for pet, task in self._all_owner_tasks():
                if task.scheduled_date and task.scheduled_time:
                    if self._to_slot(task.scheduled_date, task.scheduled_time) == slot:
                        bookings.append(self._booking_entry(pet, task))

        return {
            "slot": slot,
            "date": slot.strftime("%Y-%m-%d"),
            "time": slot.strftime("%H:%M"),
            "timezone": slot.strftime("%Z") or str(self.tz),
            "available": len(bookings) == 0,
            "bookings": sorted(bookings, key=lambda b: b["priority"], reverse=True),
        }

    def is_slot_available(self, date: datetime, time: datetime) -> bool:
        return self.get_slot_info(date, time)["available"]

    def view_tasks_by_priority(self, pets: Optional[List['Pet']] = None) -> List[dict]:
        target_pets = pets if pets is not None else list(self.owner.pets)
        for pet in target_pets:
            if pet.owner != self.owner:
                raise ValueError("You can only view tasks for your own pets.")

        entries = []
        for pet in target_pets:
            for task in pet.tasks:
                if task.scheduled_date and task.scheduled_time:
                    slot = self._to_slot(task.scheduled_date, task.scheduled_time)
                    entries.append({
                        "priority": task.priority,
                        "pet_name": pet.name,
                        "task_name": task.name,
                        "task_type": task.type.value,
                        "duration_minutes": task.duration_minutes,
                        "task_status": task.status.value,
                        "scheduled_date": task.scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": task.scheduled_time.strftime("%H:%M"),
                        "timezone": slot.strftime("%Z") or str(self.tz),
                    })

        return sorted(entries, key=lambda e: e["priority"], reverse=True)

    # ------------------------------------------------------------------
    # Scheduling mutations
    # ------------------------------------------------------------------

    def assign_task_to_schedule(self, pet: 'Pet', task: Task,
                                date: datetime, time: datetime):
        """Place a task on the schedule with timezone-aware, duration-aware validation."""
        if pet.owner != self.owner:
            raise ValueError("You can only assign tasks for your own pets.")
        if task.pet != pet:
            raise ValueError("Task must be assigned to the pet first.")
        if task.status == Status.COMPLETED:
            raise ValueError("Cannot schedule a task that is already completed.")

        candidate_slot = self._to_slot(date, time)

        self._check_time_bounds(candidate_slot, task.duration_minutes)
        self._check_overlap(pet, task, candidate_slot)

        # Store timezone-aware datetimes on the task
        task.scheduled_date = self._make_aware(date)
        task.scheduled_time = self._make_aware(time)
        task.status = (
            Status.IN_PROGRESS if candidate_slot <= self.now()
            else Status.PENDING
        )

    def move_task(self, pet: 'Pet', task: Task,
                  date: datetime, time: datetime) -> dict:
        if pet.owner != self.owner:
            raise ValueError("You can only move tasks for your own pets.")
        if task.pet != pet:
            raise ValueError("Task must be assigned to the pet first.")
        if task.status == Status.COMPLETED:
            raise ValueError("Cannot move a task that is already completed.")

        old_slot = (
            self._to_slot(task.scheduled_date, task.scheduled_time)
            if task.scheduled_date and task.scheduled_time
            else None
        )
        new_slot = self._to_slot(date, time)

        saved_date = task.scheduled_date
        saved_time = task.scheduled_time
        task.scheduled_date = None
        task.scheduled_time = None

        try:
            self._check_time_bounds(new_slot, task.duration_minutes)
            self._check_overlap(pet, task, new_slot)
        except ValueError:
            task.scheduled_date = saved_date
            task.scheduled_time = saved_time
            raise

        task.scheduled_date = self._make_aware(date)
        task.scheduled_time = self._make_aware(time)
        task.status = (
            Status.IN_PROGRESS if new_slot <= self.now()
            else Status.PENDING
        )

        return {
            "previous_slot": old_slot,
            "new_slot": new_slot,
            "status": task.status,
            "message": f"Task '{task.name}' moved from {old_slot} to {new_slot}.",
        }

    # ------------------------------------------------------------------
    # Auto-scheduling (greedy by priority)
    # ------------------------------------------------------------------

    def find_next_available_slot(
        self,
        pet: 'Pet',
        duration_minutes: int,
        start_from: Optional[datetime] = None,
        exclude_task: Optional[Task] = None,
    ) -> Optional[datetime]:
        if start_from is None:
            start_from = self.now().replace(
                hour=self.SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0
            )
        start_from = self._make_aware(start_from)

        for day in range(7):
            day_start = start_from.replace(
                hour=self.SCHEDULE_START_HOUR, minute=0, second=0, microsecond=0
            ) + timedelta(days=day)
            day_end = day_start.replace(hour=self.SCHEDULE_END_HOUR, minute=0)

            current = day_start
            while current + timedelta(minutes=duration_minutes) <= day_end:
                if self._is_slot_free(pet, current, duration_minutes, exclude_task):
                    return current
                current += timedelta(minutes=5)

        return None

    def auto_schedule(self, pets: Optional[List['Pet']] = None):
        target = pets if pets is not None else list(self.owner.pets)

        for pet in target:
            unscheduled = [
                t for t in pet.tasks
                if t.scheduled_date is None and t.status != Status.COMPLETED
            ]
            unscheduled.sort(key=lambda t: t.priority, reverse=True)

            for task in unscheduled:
                slot = self.find_next_available_slot(pet, task.duration_minutes)
                if slot:
                    task.scheduled_date = slot
                    task.scheduled_time = slot
                    task.status = (
                        Status.IN_PROGRESS if slot <= self.now()
                        else Status.PENDING
                    )

    # ------------------------------------------------------------------
    # Recurring task generation
    # ------------------------------------------------------------------

    def generate_recurring_tasks(self, pet: 'Pet', template_task: Task,
                                 days: int = 7) -> List[Task]:
        if not template_task.is_recurring():
            return []
        if template_task.scheduled_date is None or template_task.scheduled_time is None:
            return []

        intervals = {
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(days=7),
            Frequency.MONTHLY: timedelta(days=30),
        }

        if template_task.frequency == Frequency.CUSTOM:
            if template_task.repeat_interval_days:
                delta = timedelta(days=template_task.repeat_interval_days)
            else:
                return []
            max_occurrences = (template_task.repeat_count or 1) - 1
        else:
            delta = intervals.get(template_task.frequency)
            if delta is None:
                return []
            max_occurrences = days

        base_start = self._to_slot(template_task.scheduled_date,
                                   template_task.scheduled_time)
        generated: List[Task] = []
        current = base_start

        for i in range(max_occurrences):
            current = current + delta

            if current > base_start + timedelta(days=days):
                break

            new_task = Task(
                type=template_task.type,
                name=f"{template_task.name} (#{i + 2})",
                description=template_task.description,
                duration_minutes=template_task.duration_minutes,
                priority=template_task.priority,
                frequency=Frequency.ONCE,
            )

            try:
                pet.add_task(new_task)
                self.assign_task_to_schedule(pet, new_task, current, current)
                generated.append(new_task)
            except ValueError:
                fallback = self.find_next_available_slot(
                    pet,
                    new_task.duration_minutes,
                    start_from=current.replace(
                        hour=self.SCHEDULE_START_HOUR, minute=0, second=0
                    ),
                )
                if fallback and fallback.date() == current.date():
                    try:
                        self.assign_task_to_schedule(pet, new_task, fallback, fallback)
                        generated.append(new_task)
                    except ValueError:
                        pet.remove_task(new_task)
                else:
                    pet.remove_task(new_task)

        return generated

    # ------------------------------------------------------------------
    # Sorting and Filtering
    # ------------------------------------------------------------------

    def sort_tasks_by_time(self, pets: Optional[List['Pet']] = None) -> List[dict]:
        target = pets if pets is not None else list(self.owner.pets)
        entries = []

        for pet in target:
            for task in pet.tasks:
                if task.scheduled_date and task.scheduled_time:
                    start = self._to_slot(task.scheduled_date, task.scheduled_time)
                    end = start + timedelta(minutes=task.duration_minutes)
                    entries.append({
                        "pet_name": pet.name,
                        "task_name": task.name,
                        "task_type": task.type.value,
                        "priority": task.priority,
                        "duration_minutes": task.duration_minutes,
                        "status": task.status.value,
                        "frequency": task.frequency.value,
                        "scheduled_date": task.scheduled_date.strftime("%Y-%m-%d"),
                        "scheduled_time": task.scheduled_time.strftime("%H:%M"),
                        "end_time": end.strftime("%H:%M"),
                        "timezone": start.strftime("%Z") or str(self.tz),
                        "_sort_key": start,
                    })

        entries.sort(key=lambda e: e["_sort_key"])
        for e in entries:
            del e["_sort_key"]
        return entries

    def filter_tasks(
        self,
        pet: Optional['Pet'] = None,
        status: Optional['Status'] = None,
        pets: Optional[List['Pet']] = None,
    ) -> List[dict]:
        all_tasks = self.sort_tasks_by_time(pets)

        if pet is not None:
            all_tasks = [t for t in all_tasks if t["pet_name"] == pet.name]

        if status is not None:
            all_tasks = [t for t in all_tasks if t["status"] == status.value]

        return all_tasks

    # ------------------------------------------------------------------
    # Lightweight Conflict Detection
    # ------------------------------------------------------------------

    def detect_conflicts(self, pets: Optional[List['Pet']] = None) -> List[str]:
        target = pets if pets is not None else list(self.owner.pets)
        warnings: List[str] = []

        scheduled = []
        for pet in target:
            for task in pet.tasks:
                if (
                    task.scheduled_date
                    and task.scheduled_time
                    and task.status != Status.COMPLETED
                ):
                    start = self._to_slot(task.scheduled_date, task.scheduled_time)
                    end = start + timedelta(minutes=task.duration_minutes)
                    scheduled.append({
                        "pet": pet,
                        "task": task,
                        "start": start,
                        "end": end,
                    })

        seen = set()
        for i, a in enumerate(scheduled):
            for j, b in enumerate(scheduled):
                if i >= j:
                    continue

                if a["start"] < b["end"] and a["end"] > b["start"]:
                    pair_key = (id(a["task"]), id(b["task"]))
                    if pair_key in seen:
                        continue
                    seen.add(pair_key)

                    conflict_type = (
                        "SAME PET" if a["pet"] is b["pet"] else "CROSS-PET"
                    )

                    warnings.append(
                        f"⚠️  [{conflict_type}] '{a['task'].name}' for {a['pet'].name} "
                        f"({a['start'].strftime('%H:%M')}–{a['end'].strftime('%H:%M')}) "
                        f"overlaps with '{b['task'].name}' for {b['pet'].name} "
                        f"({b['start'].strftime('%H:%M')}–{b['end'].strftime('%H:%M')}) "
                        f"on {a['start'].strftime('%Y-%m-%d')} [{a['start'].strftime('%Z')}]"
                    )

        return warnings

    # ------------------------------------------------------------------
    # Complete & Auto-Renew Recurring Tasks
    # ------------------------------------------------------------------

    def complete_and_renew(self, pet: 'Pet', task: Task) -> Optional[Task]:
        task.complete_task()

        if not task.is_recurring():
            return None
        if not task.needs_more_occurrences():
            return None
        if task.scheduled_date is None or task.scheduled_time is None:
            return None

        interval_map = {
            Frequency.DAILY: timedelta(days=1),
            Frequency.WEEKLY: timedelta(days=7),
            Frequency.MONTHLY: timedelta(days=30),
        }

        if task.frequency == Frequency.CUSTOM:
            if task.repeat_interval_days:
                delta = timedelta(days=task.repeat_interval_days)
            else:
                return None
        else:
            delta = interval_map.get(task.frequency)
            if delta is None:
                return None

        current_start = self._to_slot(task.scheduled_date, task.scheduled_time)
        next_start = current_start + delta

        new_task = Task(
            type=task.type,
            name=task.name,
            description=task.description,
            duration_minutes=task.duration_minutes,
            priority=task.priority,
            frequency=task.frequency,
            repeat_count=task.repeat_count,
            repeat_interval_days=task.repeat_interval_days,
            occurrences_completed=task.occurrences_completed,
        )

        try:
            pet.add_task(new_task)
            self.assign_task_to_schedule(pet, new_task, next_start, next_start)
            return new_task
        except ValueError:
            fallback = self.find_next_available_slot(
                pet,
                new_task.duration_minutes,
                start_from=next_start.replace(
                    hour=self.SCHEDULE_START_HOUR, minute=0, second=0
                ),
            )
            if fallback:
                try:
                    self.assign_task_to_schedule(pet, new_task, fallback, fallback)
                    return new_task
                except ValueError:
                    pet.remove_task(new_task)
                    return None
            else:
                pet.remove_task(new_task)
                return None

    # ------------------------------------------------------------------
    # Notifications
    # ------------------------------------------------------------------

    def get_upcoming_tasks(self, hours: int = 24) -> List[dict]:
        now = self.now()
        window_end = now + timedelta(hours=hours)
        upcoming = []

        for pet, task in self._all_owner_tasks():
            if task.scheduled_date and task.scheduled_time:
                start = self._to_slot(task.scheduled_date, task.scheduled_time)
                if now <= start <= window_end and task.status != Status.COMPLETED:
                    upcoming.append({
                        "pet_name": pet.name,
                        "task_name": task.name,
                        "task_type": task.type.value,
                        "scheduled": start.strftime("%Y-%m-%d %H:%M %Z"),
                        "priority": task.priority,
                        "minutes_until": int((start - now).total_seconds() / 60),
                    })

        return sorted(upcoming, key=lambda x: x["minutes_until"])

    def get_overdue_tasks(self) -> List[dict]:
        overdue = []

        for pet, task in self._all_owner_tasks():
            if task.is_due() and task.status != Status.COMPLETED:
                start = self._to_slot(task.scheduled_date, task.scheduled_time)
                overdue.append({
                    "pet_name": pet.name,
                    "task_name": task.name,
                    "task_type": task.type.value,
                    "was_scheduled": start.strftime("%Y-%m-%d %H:%M %Z"),
                    "priority": task.priority,
                    "status": task.status.value,
                })

        return sorted(overdue, key=lambda x: x["priority"], reverse=True)

    # ------------------------------------------------------------------
    # Schedule explanation
    # ------------------------------------------------------------------

    def explain_schedule(self, pets: Optional[List['Pet']] = None) -> List[str]:
        entries = self.view_tasks_by_priority(pets)
        explanations = []

        for i, e in enumerate(entries, 1):
            explanations.append(
                f"{i}. '{e['task_name']}' for {e['pet_name']} is scheduled at "
                f"{e['scheduled_time']} {e.get('timezone', '')} on {e['scheduled_date']}. "
                f"This {e['task_type'].lower()} task was given priority "
                f"{e['priority']}/10 and takes {e['duration_minutes']} minute(s). "
                f"It was placed at this time because it is the earliest available "
                f"slot that fits its duration without conflicts. "
                f"(Status: {e['task_status']})"
            )

        if not explanations:
            explanations.append("No tasks are currently scheduled.")

        return explanations